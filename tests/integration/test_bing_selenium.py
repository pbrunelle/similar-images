import os

import pytest

from similar_images.bing_selenium import BingSelenium


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


@pytest.mark.asyncio
async def test_bing_search_images(headless_browser):
    # GIVEN
    query = "dog"
    n = 10
    # WHEN
    links = []
    async for link in headless_browser.search_images(query, n):
        links.append(link)
        if len(links) >= n:
            break
    # THEN
    assert len(links) > 0
    assert all(
        link.startswith("https://") or link.startswith("http://") for link in links
    )


@pytest.mark.asyncio
async def test_bing_search_similar_images_path(visual_browser):
    # GIVEN
    path = os.environ.get(
        "TEST_BING_SEARCH_SIMILAR_IMAGES_PATH",
        os.path.abspath("tests/integration/data/dog.jpg"),
    )
    n = 10
    # WHEN
    links = []
    async for link in visual_browser.search_similar_images(path, n):
        links.append(link)
        if len(links) >= n:
            break
    # THEN
    assert len(links) > 0
    assert all(
        link.startswith("https://") or link.startswith("http://") for link in links
    )


@pytest.mark.asyncio
async def test_bing_search_similar_images_url(visual_browser):
    # GIVEN
    url = os.environ.get(
        "TEST_BING_SEARCH_SIMILAR_IMAGES_URL",
        "https://upload.wikimedia.org/wikipedia/commons/a/a9/20170721_Gotham_Shield_NYC_Aerials-221_medium.jpg",
    )
    n = 10
    # WHEN
    links = []
    async for link in visual_browser.search_similar_images(url, n):
        links.append(link)
        if len(links) >= n:
            break  # THEN
    assert len(links) > 0
    assert all(
        link.startswith("https://") or link.startswith("http://") for link in links
    )
