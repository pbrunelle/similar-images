from typing import Any
import asyncio
import httpx
import hashlib
from PIL import Image
import io
from similar_images.crappy_db import CrappyDB
from similar_images.types import Result
import datetime

class Scraper:

    def __init__(self, browser: Any, client: httpx.AsyncClient | None = None):
        self.browser = browser
        self.client = client if client else httpx.AsyncClient(
            follow_redirects=True, timeout=30)

    def scrape(
        self,
        queries: list[str],
        outdir: str,
        count: int,
        db: CrappyDB | None = None,
    ) -> list[str]:
        return asyncio.run(self.scrape_async(queries, outdir, count, db))

    async def scrape_async(
        self,
        queries: list[str],
        outdir: str,
        count: int,
        db: CrappyDB | None,
    ) -> list[str]:
        all_results = []
        for query in queries:
            links = list(self.browser.search_images(query, count))
            if db:
                filtered = []
                for link in links:
                    record = db.get("url", link)
                    if not record:
                        filtered.append(link)
                    else:
                        print(f"Already downloaded: {link}: {record}")
                links = filtered
            tasks = [self.download(link, outdir, db) for link in links]
            results = await asyncio.gather(*tasks)
            results = [r for r in results if r and r not in all_results]
            all_results.extend(results)
            print(f"{query=}: {len(results)}/{len(links)} -> {len(all_results)}")
            if not results:
                break  # scrolled to the bottom of the page
            if len(all_results) >= count:
                break  # collected enough images
        return all_results

    async def download(self, link: str, outdir: str, db: CrappyDB | None) -> str | None:
        try:
            response = await self.client.get(link)
            response.raise_for_status()
            contents = response.content
            # https://stackoverflow.com/a/64994148
            hashstr = hashlib.sha256(contents).hexdigest()
            if db:
                record = db.get("hashstr", hashstr)
                if record:
                    print(f"Already downloaded: {hashstr}: {record}")
                    return None
            img = Image.open(io.BytesIO(contents))
            size = sorted(img.size)
            MIN_SIZE = sorted((640, 480))
            if size[0] < MIN_SIZE[0] or size[1] < MIN_SIZE[1]:
                print(f"Too small: {link}: {img.size}")
                return None
            filename = hashstr[:8]
            extension = img.format.lower()
            image_path = f"{outdir}/{filename}.{extension}"
            with open(image_path, 'wb') as f:
                f.write(contents)
            # print(f"Downloaded {link} to {image_path}")
            if db:
                db.put(Result(url=link, hashstr=hashstr, ts=datetime.datetime.now(), path=image_path))
            return image_path
        except Exception as e:
            print(f"Failed to download {link}: {type(e)} {e}")
            return None
