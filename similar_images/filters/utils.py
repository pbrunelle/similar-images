from similar_images.crappy_db import CrappyDB
from similar_images.filters.db_filters import (
    DbExactDupFilter,
    DbNearDupFilter,
    DbUrlFilter,
)
from similar_images.filters.filter import Filter
from similar_images.filters.gemini_filters import GeminiFilter
from similar_images.filters.image_filters import ImageFilter
from similar_images.types import CommonConfiguration


def get_filters(config: CommonConfiguration, db: CrappyDB | None) -> list[Filter]:
    if not config.filters:
        return []
    ret = []
    for filter_group in config.filters:
        for filter_name, filter_config in filter_group.items():
            match filter_name:
                case "DbUrlFilter":
                    assert db
                    ret.append(DbUrlFilter(db))
                case "DbExactDupFilter":
                    assert db
                    ret.append(DbExactDupFilter(db))
                case "DbNearDupFilter":
                    assert db
                    ret.append(DbNearDupFilter(db))
                case "ImageFilter":
                    ret.append(ImageFilter(**filter_config))
                case "GeminiFilter":
                    ret.append(GeminiFilter(**filter_config))
    return ret
