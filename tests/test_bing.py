from similar_images.bing import Bing


def _test_bing_search_images():
    # GIVEN
    ddg = Bing()
    query = "dog"
    # WHEN
    links = ddg.search_images(query)
    # THEN
    print(f"Found {len(links)} links")
    assert len(links) > 0
    assert all(
        link.startswith("https://") or link.startswith("http://") for link in links
    )
