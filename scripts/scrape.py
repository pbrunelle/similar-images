from similar_images.bing_selenium import BingSelenium
from similar_images.scraper import Scraper
from pathlib import Path
import fire

def scrape(queries_str: str, outdir: str, count: int):
    queries = queries_str.split(",")
    print(f"Scraping {queries=} to {outdir=} with {count=}")
    browser = BingSelenium()
    scraper = Scraper(browser=browser)
    Path(outdir).mkdir(parents=True, exist_ok=True)
    scraper.scrape(queries=queries, outdir=outdir, count=count)

if __name__ == "__main__":
    fire.Fire(scrape)