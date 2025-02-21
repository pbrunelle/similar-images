import logging
import os
import tempfile

import fire

from similar_images.bing_selenium import BingSelenium
from similar_images.crappy_db import CrappyDB
from similar_images.filters.db_filters import (
    DbExactDupFilter,
    DbNearDupFilter,
    DbUrlFilter,
)
from similar_images.filters.image_filters import ImageFilter
from similar_images.image_sources import BrowserQuerySource
from similar_images.scraper import Scraper

logger = logging.getLogger()


def setup_logging(verbose: bool) -> None:
    handlers = [logging.StreamHandler()]
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s.%(msecs)03d - %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    for module in [
        "asyncio",
        "selenium.webdriver.common.selenium_manager",
        "selenium.webdriver.common.service",
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


def scrape(
    queries: str,
    db: str | None = None,
    min_area: int | None = None,
    min_size: list[int] | None = None,
    num_images: int | None = None,
    outdir: str | None = None,
    threads: int | None = None,
    verbose: bool | None = None,
) -> None:
    setup_logging(verbose or False)
    logger.info(f"{queries=}")
    crappy_db = None
    filter_objects = []
    if db:
        crappy_db = CrappyDB(db)
        filter_objects += [
            DbUrlFilter(crappy_db),
            DbExactDupFilter(crappy_db),
            DbNearDupFilter(crappy_db),
        ]
    if min_size or min_area:
        min_size = tuple(min_size) if min_size else (640, 480)
        min_area = min_area or 0
        filter_objects.append(ImageFilter(min_size=min_size, min_area=min_area))
    home_tmp_dir = tempfile.mkdtemp(dir=os.environ["HOME"])
    browser = BingSelenium(user_data_dir=home_tmp_dir)
    image_source = BrowserQuerySource(browser, queries)
    scraper = Scraper(
        image_source=image_source,
        db=crappy_db,
        filters=filter_objects,
        outdir=outdir or ".",
        count=num_images,
        concurrency=threads,
    )
    scraper.sync_scrape()


if __name__ == "__main__":
    fire.Fire(scrape)
