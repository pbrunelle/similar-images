from unittest.mock import Mock

from scripts.scrape import get_filters
from similar_images.types import CommonConfiguration, ScrapeConfiguration


def test_scrape_filters():
    # GIVEN
    common_config = CommonConfiguration(
        filters={
            "DbUrlFilter": {},
            "DbExactDupFilter": {},
            "DbNearDupFilter": {},
            "ImageFilter": {
                "min_size": [600, 800],
                "min_area": 550_000,
            },
            "UnknownFilter": {},
        }
    )
    # WHEN
    filters = get_filters(common_config, db=Mock())
    # THEN
    got = [type(f).__name__ for f in filters]
    expected = [
        "DbUrlFilter",
        "DbExactDupFilter",
        "DbNearDupFilter",
        "ImageFilter",
    ]
    assert got == expected
    assert filters[3]._min_size == (600, 800)
    assert filters[3]._min_area == 550_000
