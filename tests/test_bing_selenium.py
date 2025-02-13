from similar_images.bing_selenium import BingSelenium
import os
import tempfile

def test_bing_search_images():
    with tempfile.TemporaryDirectory(dir=os.environ['HOME']) as user_data_dir:
        # GIVEN
        bing = BingSelenium(headless=True, user_data_dir=user_data_dir)
        query = "dog"
        # WHEN
        links = list(bing.search_images(query, max_images=10))
        # THEN
        print(f"Found {len(links)} links")
        print(links)
        assert len(links) > 0
        assert all(link.startswith("https://") or link.startswith("http://") for link in links)
