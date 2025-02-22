#!/usr/bin/env python3

import json
import logging
import os
import tempfile

from typer import Option, Typer

from similar_images.bing_selenium import BingSelenium
from similar_images.crappy_db import CrappyDB
from similar_images.filters.db_filters import (
    DbExactDupFilter,
    DbNearDupFilter,
    DbUrlFilter,
)
from similar_images.filters.gemini_filters import GeminiFilter
from similar_images.filters.image_filters import ImageFilter
from similar_images.image_sources import (
    BrowserImageSource,
    BrowserQuerySource,
    LocalFileImageSource,
)
from similar_images.scraper import Scraper

logger = logging.getLogger()
app = Typer()


def setup_logging(verbose: bool, logfile: str | None) -> None:
    handlers = [logging.StreamHandler()]
    if logfile:
        handlers.append(logging.FileHandler(logfile))
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


@app.command()
def scrape(
    db: str | None = None,
    debug_outdir: str | None = Option(None, "-D"),
    gemini: list[str] | None = Option(
        None, "-g", help="Run Gemini filters. You must export your GEMINI_API_KEY."
    ),
    local_files: list[str] | None = Option(None, "-l"),
    logfile: str | None = Option(None, "-L", "--logfile"),
    min_area: int | None = None,
    min_size: int | None = Option(
        None, parser=lambda arg: (int(x) for x in arg.split(","))
    ),
    num_images: int | None = Option(None, "-n"),
    outdir: str | None = Option(None, "-o"),
    paths: list[str] | None = Option(None, "-p"),
    queries: str | None = Option(None, "-q"),
    no_safe_search: bool = False,
    randomize: bool = Option(False, "-r"),
    threads: int | None = Option(None, "-t"),
    verbose: bool = Option(False, "-v"),
    visible: bool = Option(False, "--visible", help="Run browser in visual mode"),
    wait_between_scroll: int | None = Option(None, "--wait-between-scroll"),
    wait_first_load: int | None = Option(None, "--wait-first-load"),
) -> None:
    setup_logging(verbose, logfile)
    headless = not visible
    logger.info(
        f"{db=} {gemini=} {headless=} {min_area=} {min_size=} {no_safe_search=} {num_images=} {outdir=} {paths=} {queries=} {randomize=} {threads=} {verbose=}"
    )
    assert local_files or paths or queries, (
        "at least one of -l, -p or -q must be specified"
    )
    # Filters
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
    if gemini:
        for config in gemini:
            with open(config, "rt") as f:
                d = json.loads(f.read())
                filter_objects.append(GeminiFilter(**d))
    home_tmp_dir = tempfile.mkdtemp(dir=os.environ["HOME"])
    browser = BingSelenium(
        headless=headless,
        user_data_dir=home_tmp_dir,
        wait_between_scroll=wait_between_scroll,
        wait_first_load=wait_first_load,
        safe_search=not no_safe_search,
    )
    # Image sources
    image_sources = []
    if local_files:
        image_sources.append(LocalFileImageSource(local_files, random=randomize))
    if paths:
        image_sources.append(BrowserImageSource(browser, paths, random=randomize))
    if queries:
        image_sources.append(BrowserQuerySource(browser, queries))
    for image_source in image_sources:
        scraper = Scraper(
            image_source=image_source,
            db=crappy_db,
            filters=filter_objects,
            outdir=outdir or ".",
            debug_outdir=debug_outdir,
            count=num_images,
            concurrency=threads,
        )
        scraper.sync_scrape()


if __name__ == "__main__":
    app()
