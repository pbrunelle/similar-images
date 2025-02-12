from typing import Any
import asyncio
import httpx
import hashlib
from PIL import Image
import io
from similar_images.crappy_db import CrappyDB
from similar_images.types import Result
import datetime
import exrex
import logging
from pydantic import BaseModel

logger = logging.getLogger()

class DownloadResponse(BaseModel):
    image_path: str | None = None
    dup_hashstr: bool = False
    small: bool = False
    err: bool = False

class Scraper:

    def __init__(self, browser: Any, client: httpx.AsyncClient | None = None):
        self.browser = browser
        self.client = client if client else httpx.AsyncClient(
            follow_redirects=True, timeout=30)

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
        for query in exrex.generate(queries):
            query = query.strip()
            links = set(self.browser.search_images(query, count))
            n_total = len(links)
            if db:
                filtered = set()
                for link in links:
                    record = db.get("url", link)
                    if not record:
                        filtered.add(link)
                    else:
                        logger.debug(f"Already downloaded (URL): {link}: {record}")
                links = filtered
            n_downloaded = n_total - len(links)
            tasks = [self.download(link, outdir, db) for link in links]
            results = await asyncio.gather(*tasks)
            n_hash = len([r for r in results if r.dup_hashstr])
            n_small = len([r for r in results if r.small])
            n_err = len([r for r in results if r.err])
            results = set([r.image_path for r in results if r.image_path])
            all_results = all_results.union(results)
            logger.info(f"Done {query=} | links={n_total} | dup:url={n_downloaded} dup:hash={n_hash} small={n_small} err={n_err} new={len(results)} | run={len(all_results)}")
            if len(all_results) >= count:
                break  # collected enough images
        return all_results

    async def download(self, link: str, outdir: str, db: CrappyDB | None) -> DownloadResponse:
        try:
            response = await self.client.get(link)
            response.raise_for_status()
            contents = response.content
            # https://stackoverflow.com/a/64994148
            hashstr = hashlib.sha256(contents).hexdigest()
            if db:
                record = db.get("hashstr", hashstr)
                if record:
                    logger.debug(f"Already downloaded (hashstr): {link}: {record}")
                    return DownloadResponse(hashstr=True)
            img = Image.open(io.BytesIO(contents))
            size = sorted(img.size)
            MIN_SIZE = sorted((640, 480))
            if size[0] < MIN_SIZE[0] or size[1] < MIN_SIZE[1]:
                logger.debug(f"Too small: {link}: {img.size}")
                return DownloadResponse(small=True)
            filename = hashstr[:8]
            extension = img.format.lower()
            image_path = f"{outdir}/{filename}.{extension}"
            with open(image_path, 'wb') as f:
                f.write(contents)
            logger.debug(f"Downloaded {link} to {image_path}")
            if db:
                db.put(Result(url=link, hashstr=hashstr, ts=datetime.datetime.now(), path=image_path))
            return DownloadResponse(image_path=image_path)
        except Exception as e:
            str_e = str(e).replace('\n', ' ')
            logger.debug(f"Failed to download {link}: {type(e)} {str_e}")
            return DownloadResponse(err=True)
