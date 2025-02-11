from similar_images.bing_selenium import BingSelenium
from similar_images.scraper import Scraper
from similar_images.crappy_db import CrappyDB
from similar_images.types import ScrapeConfiguration
from pathlib import Path
import fire
import logging

def scrape(configfile: str) -> None:
    with open(configfile, "r") as f:
        scrape_config = ScrapeConfiguration.model_validate_json(f.read())
    #logging.basicConfig(format='%(asctime)s:%(filename)s:%(levelname)s:%(message)s',filename=log_file, level=logging.INFO, force=True)
    for run in scrape_config.runs:
        run.resolve(scrape_config.common)
        print(f"Scraping {run=}")
        db = CrappyDB(run.database)
        browser = BingSelenium(
            wait_first_load=run.wait_first_load,
            wait_between_scroll=run.wait_between_scroll,
            safe_search=run.safe_search,
            headless=run.headless
        )
        scraper = Scraper(browser=browser)
        Path(run.outdir).mkdir(parents=True, exist_ok=True)
        scraper.scrape(queries=[run.query], outdir=run.outdir, count=run.count, db=db)

if __name__ == "__main__":
    fire.Fire(scrape)