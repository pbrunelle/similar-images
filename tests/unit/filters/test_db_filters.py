import pytest

from similar_images.crappy_db import CrappyDB
from similar_images.filters.db_filters import (
    DbExactDupFilter,
    DbNearDupFilter,
    DbUrlFilter,
    hash_distance,
    near_duplicate_hash,
)
from similar_images.filters.filter import FilterResult, FilterStage
from similar_images.types import Result


@pytest.fixture
def db(tmp_path):
    db = CrappyDB(tmp_path / "db.jsonl")
    db.put(
        Result(
            url="http1",
            hashstr="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        )
    )
    db.put(Result(url="http2", hashstr="abcd"))
    db.put(
        Result(
            url="http3",
            hashstr="zzz",
            hashes={"a": "0f2787ff93c5c3c1", "p": "b617333949f8383c"},
        )
    )
    db.put(
        Result(
            url="http5",
            hashstr="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            hashes={"a": "03200040006"},
        )
    )
    yield db


@pytest.mark.parametrize(
    "url,expected", [("http1", False), ("http5", False), ("http4", True), ("", True)]
)
@pytest.mark.asyncio
async def test_db_filter_url(db, url, expected):
    # GIVEN
    db_filter = DbUrlFilter(db=db)
    # WHEN
    result = await db_filter.filter(url=url)
    # THEN
    assert result.keep == expected


@pytest.mark.parametrize(
    "contents,expected",
    [
        ("http1", True),
        ("http2", True),
        ("2cf", True),
        ("abcd", True),
        # hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        ("hello", False),
        # hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ("", False),
    ],
)
@pytest.mark.asyncio
async def test_db_filter_exact_dup(db, contents, expected):
    # GIVEN
    db_filter = DbExactDupFilter(db=db)
    # WHEN
    result = await db_filter.filter(contents=contents.encode("utf-8"), url="extra")
    # THEN
    assert result.keep == expected


@pytest.mark.parametrize(
    "hashes,expected",
    [
        ({}, True),
        ({"a": "073787df9182c1c1", "p": "bc863347dbf0382c"}, True),
        ({"a": "0f2787ff93c5c3c1", "p": "b617333949f8383c"}, False),
        ({"a": "02200040006"}, False),
    ],
)
@pytest.mark.asyncio
async def test_db_filter_near_dup(db, hashes, expected):
    # GIVEN
    db_filter = DbNearDupFilter(db=db)
    # WHEN
    result = await db_filter.filter(hashes=hashes, url="extra")
    # THEN
    assert result.keep == expected


@pytest.mark.parametrize(
    "hash1,hash2,expected",
    [
        ("0f2787ff93c5c3c1", "073787df9182c1c1", 9),
        ("b617333949f8383c", "bc863347dbf0382c", 16),
        ("d84c2ca0661d1e9b", "4c6c37bd2316070b", 23),
        ("3793f83285c98b70", "b781cc3881c6f50d", 25),
        ("0f2707ff82c5c3c1", "073787dfb083e1c1", 12),
        ("03200040006", "02200040006", 1),
        ("18187878f6103020", "18187878f6103020", 0),
        ("cc991f36e2233366", "c8991f36e2233376", 2),
        ("dbe16df706186228", "db6369f706186228", 3),
        ("db6369f706186228", "fbe16df70618622c", 5),
    ],
)
def test_hash_distance(hash1, hash2, expected):
    assert hash_distance(hash1, hash2) == expected


@pytest.mark.parametrize(
    "hashes1,hashes2,expected",
    [
        ({}, {}, False),
        (
            {"a": "0f2787ff93c5c3c1", "p": "b617333949f8383c"},
            {"a": "073787df9182c1c1", "p": "bc863347dbf0382c"},
            False,
        ),
        (
            {"a": "03200040006"},
            {"a": "02200040006"},
            True,
        ),
        (
            {"a": "cc991f36e2233366", "p": "dbe16df706186228"},
            {"a": "c8991f36e2233376", "p": "db6369f706186228"},
            True,
        ),
    ],
)
def test_near_dupolicate_hash(hashes1, hashes2, expected):
    assert near_duplicate_hash(hashes1, hashes2) == expected
