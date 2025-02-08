from typing import Any
import asyncio
import httpx


class Scraper:

    def __init__(self, browser: Any, client: httpx.AsyncClient | None = None):
        self.browser = browser
        self.client = client if client else httpx.AsyncClient(follow_redirects=True, timeout=30)

    def scrape(self, query: str, outdir: str) -> list[str]:
        return asyncio.run(self.scrape_async(query, outdir))

    async def scrape_async(self, query: str, outdir: str) -> list[str]:
        links = self.browser.search_images(query)  # TODO: asyncio
        tasks = [self.download(link, outdir) for link in links]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result]

    async def download(self, link: str, outdir: str) -> str | None:
        try:
            response = await self.client.get(link)
            response.raise_for_status()
            image_path = f"{outdir}/{link.split('/')[-1].split('?')[0]}"
            with open(image_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded {link} to {image_path}")
            return image_path
        except Exception as e:
            print(f"Failed to download {link}: {type(e)} {e}")
            return None
