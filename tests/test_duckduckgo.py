from similar_images.duckduckgo import DuckDuckGo
import pytest

@pytest.mark.skip(reason="DDG is more complicated to scrape")
def test_ddd_search_images():
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