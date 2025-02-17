import asyncio
import datetime
import functools
import hashlib
import io
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import exrex
import httpx
import imagehash
from PIL import Image

from similar_images.crappy_db import CrappyDB
from similar_images.filters.filter import Filter
from similar_images.types import Result
from similar_images.utils import get_urls_or_files

logger = logging.getLogger()


def _empty_stats(stage2filters: dict[str, list[Filter]]) -> dict[str, int]:
    ret: dict[str, int] = defaultdict(int)
    ret["links"] = 0
    for stage, filters in stage2filters.items():
        for filter in filters:
            ret[filter.stat_name()] = 0
    ret["err"] = 0
    ret["new"] = 0
    return ret


def _add_stats(stats: dict[str, int], other_stats: dict[str, int]):
    for k, v in other_stats.items():
        stats[k] += v


def _print_stats(stats: dict[str, int]) -> str:
    # "links=100 | dup:url=50 dup:hash=1 dup:near=9 small=20 llm=5 err=3 | new=12"
    parts = []
    parts.append(f"links:{stats.get('links', 0)}")
    parts.append("|")
    for stat_name, count in stats.items():
        if stat_name not in ("links", "new"):
            parts.append(f"{stat_name}:{count}")
    parts.append("|")
    parts.append(f"new:{stats.get('new', 0)}")
    return " ".join(parts)


def _update_stats(
    task: asyncio.Task, q_stats: dict[str, int], downloaded_links: set[str]
) -> None:
    q_stats["links"] += 1
    link, code = task.result()
    if link:
        downloaded_links.add(link)
    assert code
    q_stats[code] += 1


def _query_generator(queries: str):
    for query in exrex.generate(queries):
        query = query.strip()
        yield query


def _save_file(
    url: str,
    contents: bytes,
    hashstr: str,
    img: Image,
    outdir: str,
    code: str | None = None,
) -> str:
    filename = hashstr[:8]
    extension = img.format.lower()
    path = Path(outdir) if not code else Path(outdir) / code
    path.mkdir(parents=True, exist_ok=True)
    image_path = path / f"{filename}.{extension}"
    with open(image_path, "wb") as f:
        f.write(contents)
    logger.debug(f"{'Downloaded' if not code else 'Dumped'} {url} to {image_path}")
    return str(image_path)


async def _apply_filters(
    *args, filters: list[Filter], debug_outdir: str | None = None, **kwargs
) -> tuple[bool, str | None]:
    for filter in filters:
        filter_result = await filter.filter(**kwargs)
        if not filter_result.keep:
            logger.debug(filter_result.explanation)
            if (
                filter.allow_debug_rejected()
                and debug_outdir
                and "url" in kwargs
                and "contents" in kwargs
                and "hashstr" in kwargs
                and "img" in kwargs
            ):
                _save_file(
                    kwargs["url"],
                    kwargs["contents"],
                    kwargs["hashstr"],
                    kwargs["img"],
                    debug_outdir,
                    code=filter.stat_name(),
                )
            return (False, filter.stat_name())
    return (True, None)


class Scraper:
    def __init__(
        self,
        browser: Any,
        client: httpx.AsyncClient | None = None,
        db: CrappyDB | None = None,
        filters: list[Filter] | None = None,
        debug_outdir: str | None = None,
    ):
        self.browser = browser
        self.client = client or httpx.AsyncClient(follow_redirects=True, timeout=30)
        self.db = db
        self.debug_outdir = debug_outdir
        self.stage2filters: dict[str, list[Filter]] = defaultdict(list)
        if filters:
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
                    get_urls_or_files(similar_images, self.db),
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
        run_stats = _empty_stats(self.stage2filters)
        q = 0
        for query in queries:
            q += 1
            q_stats = _empty_stats(self.stage2filters)
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
                logger.debug(f"Failed to fetch {link}: no contents")
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
                hashstr=hashstr,
                img=img,
                filters=self.stage2filters["contents"],
                debug_outdir=self.debug_outdir,
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
                hashstr=hashstr,
                img=img,
                hashes=hashes,
                filters=self.stage2filters["hashes"],
                debug_outdir=self.debug_outdir,
            )
            if not keep:
                return (None, code)

            # Run expensive filters (e.g. LLMs)
            keep, code = await _apply_filters(
                url=link,
                query=query,
                contents=contents,
                hashstr=hashstr,
                img=img,
                hashes=hashes,
                filters=self.stage2filters["expensive"],
                debug_outdir=self.debug_outdir,
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
                return (None, code)

            image_path = _save_file(link, contents, hashstr, img, outdir)

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
