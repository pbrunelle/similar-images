from similar_images.bing_selenium import BingSelenium
from similar_images.scraper import Scraper
from pathlib import Path
import fire

def scrape(queries_str: str, outdir: str, count: int,  wait_first_load: float = 2, wait_between_scroll: float = 1, safe_search: bool = True, headless: bool = True):
    queries = queries_str.split(",")
    print(f"Scraping {queries=} to {outdir=} with {count=} {'with' if safe_search else 'without'} safe search")
    browser = BingSelenium(wait_first_load=wait_first_load, wait_between_scroll=wait_between_scroll, safe_search=safe_search, headless=headless)
    scraper = Scraper(browser=browser)
    Path(outdir).mkdir(parents=True, exist_ok=True)
    scraper.scrape(queries=queries, outdir=outdir, count=count)

if __name__ == "__main__":
    fire.Fire(scrape)