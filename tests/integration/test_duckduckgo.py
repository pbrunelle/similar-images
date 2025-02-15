import pytest

from similar_images.duckduckgo import DuckDuckGo


@pytest.mark.skip(reason="DDG is more complicated to scrape")
def _test_ddd_search_images():
    # GIVEN
    ddg = DuckDuckGo()
    query = "dog"
    # WHEN
    links = ddg.search_images(query)
    # THEN
    print(links)
    assert len(links) > 0
    assert all(link.startswith("https://") for link in links)
    assert False
