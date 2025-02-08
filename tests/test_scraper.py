from similar_images.bing import Bing
from similar_images.scraper import Scraper
from pathlib import Path

def test_scraper():
    # GIVEN
    bing = Bing()
    scraper = Scraper(browser=bing)
    queries = ["cats", "dogs"]
    outdir = "testtmp"
    count = 50
    Path("testtmp").mkdir(parents=True, exist_ok=True)
    # WHEN
    filenames = scraper.scrape(queries=queries, outdir=outdir, count=count)
    # THEN
    assert len(filenames) >= count
