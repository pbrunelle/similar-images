import asyncio
import datetime
import hashlib
import io
import logging
from typing import Any

import exrex
import httpx
from PIL import Image
from pydantic import BaseModel

from similar_images.crappy_db import CrappyDB
from similar_images.types import Result

logger = logging.getLogger()


class DownloadResponse(BaseModel):
    image_path: str | None = None
    dup_hashstr: bool = False
    small: bool = False
    err: bool = False


class Statistics(BaseModel):
    links: int = 0
    dup_url: int = 0
    dup_hash: int = 0
    small: int = 0
    err: int = 0
    new: int = 0

    def add(self, other):
        self.links += other.links
        self.dup_url += other.dup_url
        self.dup_hash += other.dup_hash
        self.small += other.small
        self.err += other.err
        self.new += other.new

    def __str__(self):
        return f"links={self.links} | dup:url={self.dup_url} dup:hash={self.dup_hash} small={self.small} err={self.err} | new={self.new}"


class Scraper:
    def __init__(self, browser: Any, client: httpx.AsyncClient | None = None):
        self.browser = browser
        self.client = (
            client if client else httpx.AsyncClient(follow_redirects=True, timeout=30)
        )

    def scrape(
        self,
        queries: str,
        outdir: str,
        count: int,
        db: CrappyDB | None = None,
    ) -> list[str]:
        return asyncio.run(self.scrape_async(queries, outdir, count, db))

    async def scrape_async(
        self,
        queries: str,
        outdir: str,
        count: int,
        db: CrappyDB | None,
    ) -> set[str]:
        all_results = set()
        # for query in queries:
        run_stats = Statistics()
        for query in exrex.generate(queries):
            q_stats = Statistics()
            query = query.strip()
            links = set(self.browser.search_images(query, count))
            q_stats.links = len(links)
            if db:
                filtered = set()
                for link in links:
                    record = db.get("url", link)
                    if not record:
                        filtered.add(link)
                    else:
                        logger.debug(f"Already downloaded (URL): {link}: {record}")
                        q_stats.dup_url += 1
                links = filtered
            tasks = [self.download(link, outdir, db, query) for link in links]
            results = await asyncio.gather(*tasks)
            q_stats.dup_hash = len([r for r in results if r.dup_hashstr])
            q_stats.small = len([r for r in results if r.small])
            q_stats.err = len([r for r in results if r.err])
            results = set([r.image_path for r in results if r.image_path])
            q_stats.new = len(results)
            all_results = all_results.union(results)
            logger.info(f"Done {query=} | {q_stats}")
            run_stats.add(q_stats)
            logger.info(f"Cumulative | {run_stats} | all={len(all_results)}")
            if len(all_results) >= count:
                break  # collected enough images
        return all_results

    async def download(
        self, link: str, outdir: str, db: CrappyDB | None, query: str
    ) -> DownloadResponse:
        try:
            response = await self.client.get(link, timeout=10)
            response.raise_for_status()
            contents = response.content
            # https://stackoverflow.com/a/64994148
            hashstr = hashlib.sha256(contents).hexdigest()
            if db:
                record = db.get("hashstr", hashstr)
                if record:
                    logger.debug(f"Already downloaded (hashstr): {link}: {record}")
                    return DownloadResponse(dup_hashstr=True)
            img = Image.open(io.BytesIO(contents))
            size = sorted(img.size)
            MIN_SIZE = sorted((640, 480))
            if size[0] < MIN_SIZE[0] or size[1] < MIN_SIZE[1]:
                logger.debug(f"Too small: {link}: {img.size}")
                return DownloadResponse(small=True)
            filename = hashstr[:8]
            extension = img.format.lower()
            image_path = f"{outdir}/{filename}.{extension}"
            with open(image_path, "wb") as f:
                f.write(contents)
            logger.debug(f"Downloaded {link} to {image_path}")
            if db:
                db.put(
                    Result(
                        url=link,
                        hashstr=hashstr,
                        ts=datetime.datetime.now(),
                        path=image_path,
                        query=query,
                    )
                )
            return DownloadResponse(image_path=image_path)
        except Exception as e:
            str_e = str(e).replace("\n", " ")
            logger.debug(f"Failed to download {link}: {type(e)} {str_e}")
            return DownloadResponse(err=True)
