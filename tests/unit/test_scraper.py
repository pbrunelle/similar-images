from unittest.mock import AsyncMock, Mock

from PIL import Image

from similar_images.filters.image_filters import ImageFilter
from similar_images.scraper import Scraper


def test_apply_filters():
    # GIVEN
    scrapper = Scraper(browser=Mock(), client=AsyncMock())
    image_filter = ImageFilter((100, 100), 50_000)
    img = Image.new(mode="RGB", size=(1000, 1000))
    # WHEN
    keep, explanation = scrapper.apply_filters(
        url="http", img=img, filters=[image_filter]
    )
    # THEN
    assert keep
    assert not explanation
