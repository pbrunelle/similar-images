from similar_images.filters.filter import FilterResult, FilterStage
from similar_images.filters.db_filters import DbUrlFilter, DbExactDupFilter
import pytest
from similar_images.crappy_db import CrappyDB
from similar_images.types import Result



@pytest.fixture
def db(tmp_path):
    db = CrappyDB(tmp_path / "db.jsonl")
    db.put(Result(url="http1", hashstr="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"))
    db.put(Result(url="http2", hashstr="abcd"))
    db.put(Result(url="http3", hashstr="zzz", hashes={"a": "0f2787ff93c5c3c1", "p": "b617333949f8383c"})),
    db.put(Result(url="http5", hashstr="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", hashes={"a": "03200040006"})),
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

@pytest.mark.parametrize(
    "contents,expected",
    [
        ("http1", True),
        ("http2", True),
        ("2cf", True),
        ("abcd", True),
        ("hello", False), # hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        ("", False), # hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    ]
)
def test_db_filter_hashstr(db, contents, expected):
    # GIVEN
    db_filter = DbExactDupFilter(db=db)
    # WHEN
    result = db_filter.filter(contents=contents.encode("utf-8"), url="extra")
    # THEN
    assert result.keep == expected