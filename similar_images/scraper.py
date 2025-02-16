import asyncio
import datetime
import functools
import hashlib
import io
import logging
import os
from collections import defaultdict
from typing import Any

import exrex
import httpx
import imagehash
from PIL import Image

from similar_images.crappy_db import CrappyDB
from similar_images.filters.filter import Filter
from similar_images.types import Result
from similar_images.utils import _is_url

logger = logging.getLogger()


def _add_stats(stats: dict[str, int], other_stats: dict[str, int]):
    for k, v in other_stats.items():
        stats[k] += v


def _print_stats(stats: dict[str, int]):
    links = stats.get("links", 0)
    dup_url = stats.get("dup_url", 0)
    dup_hash = stats.get("dup_hash", 0)
    dup_near = stats.get("dup_near", 0)
    small = stats.get("small", 0)
    llm = stats.get("llm", 0)
    err = stats.get("err", 0)
    new = stats.get("new", 0)
    return f"links={links} | dup:url={dup_url} dup:hash={dup_hash} dup:near={dup_near} small={small} llm={llm} err={err} | new={new}"


def _query_generator(queries: str):
    for query in exrex.generate(queries):
        query = query.strip()
        yield query


def _get_url_from_db(path: str, db: CrappyDB | None) -> str | None:
    if not db:
        return None
    _, file = os.path.split(path)
    name, _ = os.path.splitext(file)
    for r in db.scan():
        if r.hashstr.startswith(name):
            return r.url
    return None


def _urls_or_files(queries: list[str], db: CrappyDB | None):
    for q in queries:
        if _is_url(q):
            yield q
        elif os.path.isdir(q):
            for file in os.listdir(q):
                subpath = os.path.join(q, file)
                if os.path.isfile(subpath):
                    url = _get_url_from_db(subpath, db)
                    yield url if url else subpath
        else:
            url = _get_url_from_db(q, db)
            yield url if url else q


def _update_stats(
    task: asyncio.Task, q_stats: dict[str, int], downloaded_links: set[str]
) -> None:
    q_stats["links"] += 1
    link, code = task.result()
    if link:
        downloaded_links.add(link)
    assert code
    q_stats[code] += 1


async def _apply_filters(
    *args, filters: list[Filter], **kwargs
) -> tuple[bool, str | None]:
    for filter in filters:
        filter_result = await filter.filter(**kwargs)
        if not filter_result.keep:
            logger.debug(filter_result.explanation)
            return (False, filter.stat_name())
    return (True, None)


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
        queries: str | None,
        outdir: str,
        count: int,
        similar_images: list[str] | None = None,
    ) -> set[str]:
        if queries:
            return asyncio.run(
                self.scrape_async(
                    _query_generator(queries),
                    outdir,
                    count,
                    self.browser.search_images,
                )
            )
        if similar_images:
            return asyncio.run(
                self.scrape_async(
                    _urls_or_files(similar_images, self.db),
                    outdir,
                    count,
                    self.browser.search_similar_images,
                )
            )
        return set()

    async def scrape_async(
        self,
        queries,
        outdir: str,
        count: int,
        search_fn,
    ) -> set[str]:
        all_links: set[str] = set()
        run_stats: dict[str, int] = defaultdict(int)
        q = 0
        for query in queries:
            q += 1
            q_stats: dict[str, int] = defaultdict(int)
            downloaded_links: set[str] = set()
            async with asyncio.TaskGroup() as tg:
                async for link in search_fn(query, count):
                    task = tg.create_task(
                        self.process_link(link=link, query=query, outdir=outdir)
                    )
                    task.add_done_callback(
                        functools.partial(
                            _update_stats,
                            q_stats=q_stats,
                            downloaded_links=downloaded_links,
                        )
                    )
            all_links = all_links.union(downloaded_links)
            logger.info(f"Done {query=} | {_print_stats(q_stats)}")
            _add_stats(run_stats, q_stats)
            logger.info(f"Cumulative n={q} | {_print_stats(run_stats)}")
            if len(all_links) >= count:
                break  # collected enough images
        return all_links

    async def process_link(
        self, link: str, query: str, outdir: str
    ) -> tuple[str | None, str]:
        try:
            # Filter based on URL
            keep, code = await _apply_filters(
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
            keep, code = await _apply_filters(
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
            keep, code = await _apply_filters(
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
            keep, code = await _apply_filters(
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
