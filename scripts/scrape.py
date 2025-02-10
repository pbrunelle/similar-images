from similar_images.bing_selenium import BingSelenium
from similar_images.scraper import Scraper
from pathlib import Path
import fire

def scrape(queries_str: str, outdir: str, count: int, safe_search: bool = True):
    queries = queries_str.split(",")
    print(f"Scraping {queries=} to {outdir=} with {count=} {'with' if safe_search else 'without'} safe search")
    browser = BingSelenium(safe_search=safe_search)
    scraper = Scraper(browser=browser)
    Path(outdir).mkdir(parents=True, exist_ok=True)
    scraper.scrape(queries=queries, outdir=outdir, count=count)

if __name__ == "__main__":
    fire.Fire(scrape)