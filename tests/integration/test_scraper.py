from pathlib import Path

from similar_images.bing import Bing
from similar_images.bing_selenium import BingSelenium
from similar_images.scraper import Scraper


def _test_scraper():
    # GIVEN
    # bing = Bing()
    bing = BingSelenium()
    scraper = Scraper(browser=bing)
    queries = ["cats", "dogs"]
    outdir = "testtmp"
    count = 50
    Path("testtmp").mkdir(parents=True, exist_ok=True)
    # WHEN
    filenames = scraper.scrape(queries=queries, outdir=outdir, count=count)
    # THEN
    assert len(filenames) >= count
