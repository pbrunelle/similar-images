from pathlib import Path

import pytest

from similar_images.bing_selenium import BingSelenium
from similar_images.crappy_db import CrappyDB
from similar_images.filters.db_filters import DbUrlFilter
from similar_images.filters.image_filters import ImageFilter
from similar_images.scraper import Scraper


@pytest.fixture
def browser(home_tmp_dir):
    ret = BingSelenium(
        wait_first_load=5,
        wait_between_scroll=10,
        safe_search=True,
        headless=True,
        user_data_dir=home_tmp_dir,
    )
    yield ret
    ret.done()


def test_scraper_query_search(home_tmp_dir, browser):
    # GIVEN
    db = CrappyDB(f"{home_tmp_dir}/test_db.jsonl")
    assert len(list(db.scan())) == 0
    filters = [
        DbUrlFilter(db),
        ImageFilter((100, 100), 100_000),
    ]
    scraper = Scraper(browser=browser, db=db, filters=filters)
    outdir = f"{home_tmp_dir}/dl"
    # WHEN
    filenames = scraper.scrape(
        queries="cats|dogs",
        outdir=outdir,
        count=10,
        similar_images=None,
    )
    # THEN
    assert len(filenames) > 0
    assert len(filenames) == len(list(db.scan()))


def test_scraper_similar_search(home_tmp_dir, browser):
    # GIVEN
    db = CrappyDB(f"{home_tmp_dir}/test_db.jsonl")
    assert len(list(db.scan())) == 0
    filters = [
        DbUrlFilter(db),
        ImageFilter((100, 100), 100_000),
    ]
    scraper = Scraper(browser=browser, db=db, filters=filters)
    outdir = f"{home_tmp_dir}/dl"
    # WHEN
    filenames = scraper.scrape(
        queries=None,
        outdir=outdir,
        count=10,
        similar_images=[
            "https://static01.nyt.com/images/2023/07/02/nytfrontpage/scan.jpg",
            "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png",
        ],
    )
    # THEN
    assert len(filenames) > 0
    assert len(filenames) == len(list(db.scan()))
