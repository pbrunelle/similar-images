import pytest

from similar_images.bing_selenium import BingSelenium
from similar_images.crappy_db import CrappyDB
from similar_images.filters.db_filters import DbUrlFilter
from similar_images.filters.image_filters import ImageFilter
from similar_images.image_sources import BrowserImageSource, BrowserQuerySource
from similar_images.scraper import Scraper


@pytest.fixture
def get_browser(home_tmp_dir):
    browser: BingSelenium | None = None

    def _fn(headless: bool) -> BingSelenium:
        nonlocal browser
        browser = BingSelenium(
            wait_first_load=5,
            wait_between_scroll=10,
            safe_search=True,
            headless=headless,
            user_data_dir=home_tmp_dir,
        )
        return browser

    yield _fn
    assert browser
    browser.done()


def test_scraper_query_search(home_tmp_dir, get_browser):
    # GIVEN
    browser = get_browser(True)
    src = BrowserQuerySource(browser=browser, queries="cats|dogs")
    db = CrappyDB(f"{home_tmp_dir}/test_db.jsonl")
    assert len(list(db.scan())) == 0
    filters = [
        DbUrlFilter(db),
        ImageFilter((100, 100), 100_000),
    ]
    outdir = f"{home_tmp_dir}/dl"
    scraper = Scraper(image_source=src, db=db, filters=filters, outdir=outdir, count=10)
    # WHEN
    filenames = scraper.sync_scrape()
    # THEN
    assert len(filenames) > 0
    assert len(filenames) == len(list(db.scan()))


def test_scraper_similar_search(home_tmp_dir, get_browser):
    # GIVEN
    browser = get_browser(False)
    urls = [
        "https://static01.nyt.com/images/2023/07/02/nytfrontpage/scan.jpg",
        "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png",
    ]
    src = BrowserImageSource(browser=browser, urls_or_paths=urls)
    db = CrappyDB(f"{home_tmp_dir}/test_db.jsonl")
    assert len(list(db.scan())) == 0
    filters = [
        DbUrlFilter(db),
        ImageFilter((100, 100), 100_000),
    ]
    outdir = f"{home_tmp_dir}/dl"
    scraper = Scraper(image_source=src, db=db, filters=filters, outdir=outdir, count=10)
    # WHEN
    filenames = scraper.sync_scrape()
    # THEN
    assert len(filenames) > 0
    assert len(filenames) == len(list(db.scan()))
