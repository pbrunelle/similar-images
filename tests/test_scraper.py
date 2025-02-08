from similar_images.bing import Bing
from similar_images.scraper import Scraper
from pathlib import Path

def test_scraper():
    # GIVEN
    bing = Bing()
    scraper = Scraper(browser=bing)
    query = "dog"
    outdir = "testtmp"
    Path("testtmp").mkdir(parents=True, exist_ok=True)
    # WHEN
    filenames = scraper.scrape(query=query, outdir="testtmp")
    # THEN
    assert len(filenames) > 0
    assert False
