from similar_images.bing_selenium import BingSelenium
from similar_images.scraper import Scraper
from similar_images.crappy_db import CrappyDB
from similar_images.types import ScrapeConfiguration
from pathlib import Path
import fire
import logging
import datetime

logger = logging.getLogger()

def scrape(configfile: str) -> None:
    with open(configfile, "r") as f:
        scrape_config = ScrapeConfiguration.model_validate_json(f.read())
    handlers = [
        logging.StreamHandler()
    ]
    if scrape_config.logfile:
        handlers.append(logging.FileHandler(scrape_config.logfile))
    logging.basicConfig(
        level=scrape_config.verbosity,
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )
    for module in [
        'selenium.webdriver.common.selenium_manager',
        'selenium.webdriver.remote.remote_connection',
        'urllib3.connectionpool',
        'httpcore.http11',
        'httpcore.connection',
        'httpx',
        "PIL.TiffImagePlugin",
        "PIL.PngImagePlugin",
        "PIL.Image",
    ]:
        logging.getLogger(module).disabled = True
    for run in scrape_config.runs:
        run.resolve(scrape_config.common)
        logger.info(f"Scraping {run=}")
        db = CrappyDB(run.database)
        browser = BingSelenium(
            wait_first_load=run.wait_first_load,
            wait_between_scroll=run.wait_between_scroll,
            safe_search=run.safe_search,
            headless=run.headless
        )
        scraper = Scraper(browser=browser)
        now_str = datetime.datetime.now().strftime("%Y_%m_%d-%p%I_%M_%S")
        outdir = f"{run.outdir}/{now_str}"
        Path(outdir).mkdir(parents=True, exist_ok=True)
        scraper.scrape(queries=run.queries, outdir=outdir, count=run.count, db=db)

if __name__ == "__main__":
    fire.Fire(scrape)