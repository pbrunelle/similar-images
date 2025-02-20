import datetime
import logging

import fire

from similar_images.bing_selenium import BingSelenium
from similar_images.crappy_db import CrappyDB
from similar_images.filters.utils import get_filters
from similar_images.image_sources import get_image_sources
from similar_images.scraper import Scraper
from similar_images.types import ScrapeConfiguration

logger = logging.getLogger()


def setup_logging(scrape_config: ScrapeConfiguration):
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


def scrape(configfile: str) -> None:
    with open(configfile, "r") as f:
        scrape_config = ScrapeConfiguration.model_validate_json(f.read())

    setup_logging(scrape_config)

    for run in scrape_config.runs:
        run.resolve(scrape_config.common)

        db = CrappyDB(run.database) if run.database else None
        filters = get_filters(run, db)
        image_sources = get_image_sources(run)

        logger.info(f"Scraping {run=}")
        logger.info(f"Using filters: {filters}")
        logger.info(f"Using image sources: {image_sources}")

        for image_source in image_sources:
            outdir: str | None = None
            if run.outdir:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                outdir = f"{run.outdir}/{now_str}"
            scraper = Scraper(
                image_source=image_source,
                db=db,
                filters=filters,
                outdir=outdir,
                count=run.count,
                debug_outdir=run.debug_outdir,
                concurrency=run.concurrency,
            )
            scraper.sync_scrape()
            # TODO:
            # browser.done()
            # shutil.rmtree(home_tmp_dir)


if __name__ == "__main__":
    fire.Fire(scrape)
