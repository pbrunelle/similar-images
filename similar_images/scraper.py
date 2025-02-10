from typing import Any
import asyncio
import httpx


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
            image_path = f"{outdir}/{link.split('/')[-1].split('?')[0]}"
            with open(image_path, 'wb') as f:
                f.write(response.content)
            # print(f"Downloaded {link} to {image_path}")
            return image_path
        except Exception as e:
            # print(f"Failed to download {link}: {type(e)} {e}")
            return None
