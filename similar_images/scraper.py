import asyncio
import datetime
import hashlib
import io
import logging
from collections import defaultdict
from typing import Any

import exrex
import httpx
import imagehash
from PIL import Image

from similar_images.crappy_db import CrappyDB
from similar_images.filters.filter import Filter
from similar_images.types import Result

logger = logging.getLogger()


def add_stats(stats: dict[str, int], other_stats: dict[str, int]):
    for k, v in other_stats.items():
        stats[k] += v


def print_stats(stats: dict[str, int]):
    links = stats.get("links", 0)
    dup_url = stats.get("dup_url", 0)
    dup_hash = stats.get("dup_hash", 0)
    dup_near = stats.get("dup_near", 0)
    small = stats.get("small", 0)
    llm = stats.get("llm", 0)
    err = stats.get("err", 0)
    new = stats.get("new", 0)
    return f"links={links} | dup:url={dup_url} dup:hash={dup_hash} dup:near={dup_near} small={small} llm={llm} err={err} | new={new}"


class Scraper:
    def __init__(
        self,
        browser: Any,
        client: httpx.AsyncClient | None = None,
        db: CrappyDB | None = None,
        filters: list[Filter] | None = None,
    ):
        self.browser = browser
        self.client = (
            client if client else httpx.AsyncClient(follow_redirects=True, timeout=30)
        )
        self.db = db
        filters = filters if filters else []
        self.stage2filters: dict[str, list[Filter]] = defaultdict(list)
        for filter in filters:
            self.stage2filters[filter.stage()].append(filter)

    def scrape(
        self,
        queries: str,
        outdir: str,
        count: int,
    ) -> list[str]:
        return asyncio.run(self.scrape_async(queries, outdir, count))

    async def scrape_async(
        self,
        queries: str,
        outdir: str,
        count: int,
    ) -> set[str]:
        all_links: set[str] = set()
        run_stats: dict[str, int] = defaultdict(int)
        for query in exrex.generate(queries):
            q_stats = defaultdict(int)
            query = query.strip()
            links = set(self.browser.search_images(query, count))
            tasks = [
                self.process_link(link=link, query=query, outdir=outdir)
                for link in links
            ]
            processed_links = await asyncio.gather(*tasks)
            downloaded_links = set()
            for link, code in processed_links:
                if link:
                    downloaded_links.add(link)
                assert code
                q_stats[code] += 1
            q_stats["links"] += len(downloaded_links)
            all_links = all_links.union(downloaded_links)
            logger.info(f"Done {query=} | {print_stats(q_stats)}")
            add_stats(run_stats, q_stats)
            logger.info(f"Cumulative | {print_stats(run_stats)}")
            if len(all_links) >= count:
                break  # collected enough images
        return all_links

    async def process_link(
        self, link: str, query: str, outdir: str
    ) -> tuple[str | None, str]:
        try:
            # Filter based on URL
            keep, code = await self.apply_filters(
                query=query, url=link, filters=self.stage2filters["url"]
            )
            if not keep:
                return (None, code)

            # Download image (do not save to disk yet)
            response = await self.client.get(link)
            response.raise_for_status()
            contents = response.content
            if not contents:
                return (None, "err")

            # Get image "identity"
            # https://stackoverflow.com/a/64994148
            hashstr = hashlib.sha256(contents).hexdigest()

            img = Image.open(io.BytesIO(contents))

            # Filter based on image contents
            keep, code = await self.apply_filters(
                url=link,
                query=query,
                contents=contents,
                img=img,
                filters=self.stage2filters["contents"],
            )
            if not keep:
                return (None, code)

            # Filter based on hashes
            hashes = {
                "a": str(imagehash.average_hash(img)),
                "p": str(imagehash.phash(img)),
                "d": str(imagehash.dhash(img)),
                "dv": str(imagehash.dhash_vertical(img)),
                "w": str(imagehash.whash(img)),
            }
            keep, code = await self.apply_filters(
                url=link,
                query=query,
                contents=contents,
                image=img,
                hashes=hashes,
                filters=self.stage2filters["hashes"],
            )
            if not keep:
                return (None, code)

            # Run expensive filters (e.g. LLMs)
            keep, code = await self.apply_filters(
                url=link,
                query=query,
                contents=contents,
                image=img,
                hashes=hashes,
                filters=self.stage2filters["expensive"],
            )
            if not keep:
                if self.db:
                    # Remember this image to avoid performing expensive computations again
                    self.db.put(
                        Result(
                            url=link,
                            hashstr=hashstr,
                            ts=datetime.datetime.now(),
                            path="",
                            query=query,
                            hashes=hashes,
                        )
                    )
                return (
                    None,
                    code,
                )

            # Save file
            filename = hashstr[:8]
            extension = img.format.lower()
            image_path = f"{outdir}/{filename}.{extension}"
            with open(image_path, "wb") as f:
                f.write(contents)
            logger.debug(f"Downloaded {link} to {image_path}")

            # Update DB
            if self.db:
                self.db.put(
                    Result(
                        url=link,
                        hashstr=hashstr,
                        ts=datetime.datetime.now(),
                        path=image_path,
                        query=query,
                        hashes=hashes,
                    )
                )

            return (image_path, "new")

        except Exception as e:
            str_e = str(e).replace("\n", " ")
            logger.debug(f"Failed to download {link}: {type(e)} {str_e}")
            return (None, "err")

    async def apply_filters(
        *args, filters: list[Filter], **kwargs
    ) -> tuple[bool, str | None]:
        for filter in filters:
            filter_result = await filter.filter(**kwargs)
            if not filter_result.keep:
                logger.debug(filter_result.explanation)
                return (False, filter.stat_name())
        return (True, None)
