from similar_images.filters.filter import FilterResult, FilterStage
from similar_images.filters.db_filters import DbUrlFilter
import pytest
from similar_images.crappy_db import CrappyDB
from similar_images.types import Result


@pytest.fixture
def db(tmp_path):
    db = CrappyDB(tmp_path / "db.jsonl")
    db.put(Result(url="http1", hashstr="abcd"))
    db.put(Result(url="http2", hashstr="xyz"))
    db.put(Result(url="http3", hashstr="aabbcc", hashes={"a": "0f2787ff93c5c3c1", "p": "b617333949f8383c"})),
    db.put(Result(url="http5", hashstr="aabbcc", hashes={"a": "03200040006"})),
    yield db
    
@pytest.mark.parametrize(
    "url,expected",
    [
        ("http1", False),
        ("http5", False),
        ("http4", True),
        ("", True)
    ]
)
def test_db_filter_url(db, url, expected):
    # GIVEN
    db_filter = DbUrlFilter(db=db)
    # WHEN
    result = db_filter.filter(url=url)
    # THEN
    assert result.keep == expected