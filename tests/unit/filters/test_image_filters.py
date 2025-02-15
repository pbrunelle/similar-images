import pytest
from PIL import Image

from similar_images.filters.filter import FilterResult, FilterStage
from similar_images.filters.image_filters import ImageFilter


@pytest.mark.parametrize(
    "x,y,expected",
    [
        (320, 320, False),
        (640, 480, False),
        (2000, 400, False),
        (100, 600, False),
        (600, 1000, True),
        (1000, 600, True),
        (1500, 700, True),
    ],
)
def test_image_filter(x, y, expected):
    # GIVEN
    image_filter = ImageFilter(min_size=(800, 500), min_area=600_000)
    img = Image.new(mode="RGB", size=(x, y))
    # WHEN
    result = image_filter.filter(img=img, url="http")
    # THEN
    assert result.keep == expected
