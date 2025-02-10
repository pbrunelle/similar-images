from typing import Any
import asyncio
import httpx
import hashlib
from PIL import Image
import io

class Scraper:

    def __init__(self, browser: Any, client: httpx.AsyncClient | None = None):
        self.browser = browser
        self.client = client if client else httpx.AsyncClient(
            follow_redirects=True, timeout=30)

    def scrape(
            self,
            queries: list[str],
            outdir: str,
            count) -> list[str]:
        return asyncio.run(self.scrape_async(queries, outdir, count))

    async def scrape_async(
            self,
            queries: list[str],
            outdir: str,
            count) -> list[str]:
        all_results = []
        for query in queries:
            links = list(self.browser.search_images(query, count))
            tasks = [self.download(link, outdir) for link in links]
            results = await asyncio.gather(*tasks)
            results = [r for r in results if r and r not in all_results]
            all_results.extend(results)
            print(f"{query=}: {len(results)}/{len(links)} -> {len(all_results)}")
            if not results:
                break  # scrolled to the bottom of the page
            if len(all_results) >= count:
                break  # collected enough images
        return all_results

    async def download(self, link: str, outdir: str) -> str | None:
        try:
            response = await self.client.get(link)
            response.raise_for_status()
            contents = response.content
            image_path = f"{outdir}/{self.get_filename(link, contents)}"
            with open(image_path, 'wb') as f:
                f.write(contents)
            # print(f"Downloaded {link} to {image_path}")
            return image_path
        except Exception as e:
            print(f"Failed to download {link}: {type(e)} {e}")
            return None
    
    def get_filename(self, link: str, contents: bytes) -> str:
        # https://stackoverflow.com/a/64994148
        try:
            hash = hashlib.sha256(contents).hexdigest()[:8]
            extension = Image.open(io.BytesIO(contents)).format.lower()
            return f"{hash}.{extension}"
        except Exception as e:
            print(f"Failed to get filename for {link}: {type(e)} {e}")
            raise