from similar_images.bing_selenium import BingSelenium
import os
import tempfile
import shutil
import pytest

@pytest.fixture
def home_tmp_dir():
    d = tempfile.mkdtemp(dir=os.environ['HOME'])
    yield d
    shutil.rmtree(d)

@pytest.fixture
def browser(home_tmp_dir):
    ret = BingSelenium(headless=True, user_data_dir=home_tmp_dir)
    yield ret
    ret.done()

def test_bing_search_images(browser):
    # GIVEN
    query = "dog"
    # WHEN
    links = list(browser.search_images(query, max_images=10))
    # THEN
    assert len(links) > 0
    assert all(link.startswith("https://") or link.startswith("http://") for link in links)
