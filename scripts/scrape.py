import datetime
import logging
import os
import shutil
import tempfile

import fire
import httpx

from similar_images.bing_selenium import BingSelenium
from similar_images.crappy_db import CrappyDB
from similar_images.filters.db_filters import (
    DbExactDupFilter,
    DbNearDupFilter,
    DbUrlFilter,
)
from similar_images.filters.filter import Filter
from similar_images.filters.gemini_filters import GeminiFilter
from similar_images.filters.image_filters import ImageFilter
from similar_images.scraper import Scraper
from similar_images.types import CommonConfiguration, ScrapeConfiguration

logger = logging.getLogger()


class FakeClient:
    async def get(self, url: str, *args, **kwargs):
        with open(url, "rb") as f:
            return httpx.Response(
                status_code=200,
                content=f.read(),
                request=httpx.Request(method="GET", url=f"file://{url}"),
            )


def get_filters(config: CommonConfiguration, db: CrappyDB | None) -> list[Filter]:
    if not config.filters:
        return []
    ret = []
    for filter_group in config.filters:
        for filter_name, filter_config in filter_group.items():
            match filter_name:
                case "DbUrlFilter":
                    assert db
                    ret.append(DbUrlFilter(db))
                case "DbExactDupFilter":
                    assert db
                    ret.append(DbExactDupFilter(db))
                case "DbNearDupFilter":
                    assert db
                    ret.append(DbNearDupFilter(db))
                case "ImageFilter":
                    ret.append(ImageFilter(**filter_config))
                case "GeminiFilter":
                    ret.append(GeminiFilter(**filter_config))
    return ret


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
        db = CrappyDB(run.database) if run.database else None
        filters: list[Filter] = get_filters(run, db)
        logger.info(f"Using filters: {filters}")
        home_tmp_dir = tempfile.mkdtemp(dir=os.environ["HOME"])
        browser = BingSelenium(
            wait_first_load=run.wait_first_load,
            wait_between_scroll=run.wait_between_scroll,
            safe_search=run.safe_search,
            headless=run.headless,
            user_data_dir=home_tmp_dir,
        )
        client = FakeClient() if run.evaluate_images else None
        scraper = Scraper(
            browser=browser,
            client=client,
            db=db,
            filters=filters,
            debug_outdir=run.debug_outdir,
        )
        outdir: str | None = None
        if run.outdir:
            now_str = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            outdir = f"{run.outdir}/{now_str}"
        scraper.scrape(
            queries=run.queries,
            outdir=outdir,
            count=run.count,
            similar_images=run.similar_images,
            evaluate_images=run.evaluate_images,
        )
        browser.done()
        shutil.rmtree(home_tmp_dir)


if __name__ == "__main__":
    fire.Fire(scrape)
