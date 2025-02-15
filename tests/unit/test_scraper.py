from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from similar_images.filters.image_filters import ImageFilter
from similar_images.scraper import Scraper


@pytest.mark.parametrize(
    "size,expected_keep,expected_code",
    [
        ((1000, 1000), True, None),
        ((10, 10), False, "small"),
    ],
)
def test_apply_filters(size, expected_keep, expected_code):
    # GIVEN
    scrapper = Scraper(browser=Mock(), client=AsyncMock())
    filters = [ImageFilter((100, 100), 50_000)]
    img = Image.new(mode="RGB", size=size)
    # WHEN
    keep, code = scrapper.apply_filters(url="http", img=img, filters=filters)
    # THEN
    assert keep == expected_keep
    assert code == expected_code
