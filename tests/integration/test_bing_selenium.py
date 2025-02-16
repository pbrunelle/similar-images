import os
import shutil
import tempfile

import pytest

from similar_images.bing_selenium import BingSelenium


@pytest.fixture
def home_tmp_dir():
    d = tempfile.mkdtemp(dir=os.environ["HOME"])
    yield d
    shutil.rmtree(d)


@pytest.fixture
def headless_browser(home_tmp_dir):
    ret = BingSelenium(headless=True, user_data_dir=home_tmp_dir)
    yield ret
    ret.done()


@pytest.fixture
def visual_browser(home_tmp_dir):
    ret = BingSelenium(headless=False, user_data_dir=home_tmp_dir)
    yield ret
    ret.done()


def test_bing_search_images(headless_browser):
    # GIVEN
    query = "dog"
    # WHEN
    links = list(headless_browser.search_images(query, max_images=10))
    # THEN
    assert len(links) > 0
    assert all(
        link.startswith("https://") or link.startswith("http://") for link in links
    )


def test_bing_search_similar_images_path(visual_browser):
    # GIVEN
    path = os.environ["TEST_BING_SEARCH_SIMILAR_IMAGES_PATH"]
    # WHEN
    links = list(visual_browser.search_similar_images(path, max_images=10))
    # THEN
    assert len(links) > 0
    assert all(
        link.startswith("https://") or link.startswith("http://") for link in links
    )


def test_bing_search_similar_images_url(visual_browser):
    # GIVEN
    url = os.environ["TEST_BING_SEARCH_SIMILAR_IMAGES_URL"]
    # WHEN
    links = list(visual_browser.search_similar_images(url, max_images=10))
    # THEN
    assert len(links) > 0
    assert all(
        link.startswith("https://") or link.startswith("http://") for link in links
    )
