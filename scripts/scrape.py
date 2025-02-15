import datetime
import logging
import os
import shutil
import tempfile
from pathlib import Path

import fire

from similar_images.bing_selenium import BingSelenium
from similar_images.crappy_db import CrappyDB
from similar_images.scraper import Scraper
from similar_images.types import ScrapeConfiguration
from similar_images.filters.db_filters import DbExactDupFilter, DbNearDupFilter, DbUrlFilter
from similar_images.filters.image_filters import ImageFilter
from similar_images.filters.filter import Filter

logger = logging.getLogger()


def scrape(configfile: str) -> None:
    with open(configfile, "r") as f:
        scrape_config = ScrapeConfiguration.model_validate_json(f.read())
    handlers = [logging.StreamHandler()]
    if scrape_config.logfile:
        handlers.append(logging.FileHandler(scrape_config.logfile))
    logging.basicConfig(
        level=scrape_config.verbosity,
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
        handlers=handlers,
    )
    for module in [
        "selenium.webdriver.common.selenium_manager",
        "selenium.webdriver.remote.remote_connection",
        "urllib3.connectionpool",
        "httpcore.http11",
        "httpcore.connection",
        "httpx",
        "PIL.TiffImagePlugin",
        "PIL.PngImagePlugin",
        "PIL.Image",
    ]:
        logging.getLogger(module).disabled = True

    for run in scrape_config.runs:
        run.resolve(scrape_config.common)
        logger.info(f"Scraping {run=}")
        db = CrappyDB(run.database)
        filters: list[Filter] = [
            DbUrlFilter(db),
            DbExactDupFilter(db),
            DbNearDupFilter(db),
            ImageFilter((600, 800), 600_000),
        ]
        home_tmp_dir = tempfile.mkdtemp(dir=os.environ["HOME"])
        browser = BingSelenium(
            wait_first_load=run.wait_first_load,
            wait_between_scroll=run.wait_between_scroll,
            safe_search=run.safe_search,
            headless=run.headless,
            user_data_dir=home_tmp_dir,
        )
        scraper = Scraper(browser=browser, db=db, filters=filters)
        now_str = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        outdir = f"{run.outdir}/{now_str}"
        Path(outdir).mkdir(parents=True, exist_ok=True)
        scraper.scrape(queries=run.queries, outdir=outdir, count=run.count)
        browser.done()
        shutil.rmtree(home_tmp_dir)


if __name__ == "__main__":
    fire.Fire(scrape)
