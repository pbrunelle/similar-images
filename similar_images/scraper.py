import asyncio
import datetime
import hashlib
import io
import logging
import re
from collections import defaultdict
from pathlib import Path

import httpx
import imagehash
from PIL import Image

from similar_images.crappy_db import CrappyDB
from similar_images.filters.filter import Filter
from similar_images.image_sources import ImageSource
from similar_images.types import Result

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


def _save_file(
    url: str,
    contents: bytes,
    hashstr: str,
    img: Image,
    outdir: str | None,
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
                debug_outdir
                and filter.allow_debug_rejected()
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
        image_source: ImageSource,
        client: httpx.AsyncClient | None = None,
        db: CrappyDB | None = None,
        filters: list[Filter] | None = None,
        outdir: str | None = None,
        debug_outdir: str | None = None,
        concurrency: int | None = None,
        count: int | None = None,
    ):
        self.image_source = image_source
        self.client = client or image_source.get_client()
        self.db = db
        self.outdir = outdir
        self.debug_outdir = debug_outdir
        self.stage2filters: dict[str, list[Filter]] = defaultdict(list)
        self.semaphore = asyncio.Semaphore(concurrency or 1)
        self.count = count
        if filters:
            for filter in filters:
                self.stage2filters[filter.stage()].append(filter)

    def sync_scrape(self) -> set[str]:
        return asyncio.run(self.async_scrape())

    async def async_scrape(self) -> set[str]:
        downloaded_links: set[str] = set()
        run_stats = _empty_stats(self.stage2filters)
        q = 0
        async for query in self.image_source.batches():
            q += 1
            q_stats = _empty_stats(self.stage2filters)
            try:
                async with asyncio.TaskGroup() as tg:
                    async for link in self.image_source.images(query):
                        tg.create_task(
                            self.process_link_task(
                                link, query, downloaded_links, q_stats
                            )
                        )
            except Exception as ex:
                logger.warning(f"Exception while processing {query=}: {type(ex)} {ex}")
            logger.info(f"Done {query=} | {_print_stats(q_stats)}")
            _add_stats(run_stats, q_stats)
            logger.info(f"Cumulative n={q} | {_print_stats(run_stats)}")
            if self.count is not None and len(downloaded_links) >= self.count:
                break  # collected enough images
        return downloaded_links

    async def process_link_task(
        self, link: str, query: str, downloaded_links: set[str], q_stats: dict[str, int]
    ) -> None:
        async with self.semaphore:
            if self.count is not None and q_stats["new"] >= self.count:
                return  # collected enough images
            link, code = await self.process_link(link, query)
            q_stats["links"] += 1
            if link:
                downloaded_links.add(link)
            if code:
                q_stats[code] += 1

    async def process_link(self, link: str, query: str) -> tuple[str | None, str]:
        try:
            filter_data = {"query": query, "url": link}
            # Filter based on URL
            keep, code = await _apply_filters(
                **filter_data, filters=self.stage2filters["url"]
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
            filter_data.update(
                {
                    "contents": contents,
                    "hashstr": hashstr,
                    "img": img,
                }
            )
            keep, code = await _apply_filters(
                **filter_data,
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
            filter_data.update(
                {
                    "hashes": hashes,
                }
            )
            keep, code = await _apply_filters(
                **filter_data,
                filters=self.stage2filters["hashes"],
                debug_outdir=self.debug_outdir,
            )
            if not keep:
                return (None, code)

            # Run expensive filters (e.g. LLMs)
            keep, code = await _apply_filters(
                **filter_data,
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

            image_path = None
            if self.outdir:
                image_path = _save_file(link, contents, hashstr, img, self.outdir)

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
            str_e = str(e)
            if m := re.match("(.*) for url .*", str_e):
                str_e = m.group(1)
            logger.debug(f"Failed to download {link}: {type(e).__name__} {str_e}")
            return (None, "err")
