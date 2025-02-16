import os
from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from similar_images.crappy_db import CrappyDB
from similar_images.filters.image_filters import ImageFilter
from similar_images.scraper import _apply_filters, _urls_or_files
from similar_images.types import Result


@pytest.mark.parametrize(
    "size,expected_keep,expected_code",
    [
        ((1000, 1000), True, None),
        ((10, 10), False, "small"),
    ],
)
@pytest.mark.asyncio
async def test_apply_filters(size, expected_keep, expected_code):
    # GIVEN
    filters = [ImageFilter((100, 100), 50_000)]
    img = Image.new(mode="RGB", size=size)
    # WHEN
    keep, code = await _apply_filters(url="http", img=img, filters=filters)
    # THEN
    assert keep == expected_keep
    assert code == expected_code


def test_urls_or_files(tmp_path):
    # GIVEN
    db_file = tmp_path / "test_urls_or_files.jsonl"
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir(parents=True, exist_ok=True)
    file1 = sub_dir / "xxx.png"
    file2 = sub_dir / "xyz.png"
    file1.touch()
    file2.touch()
    db = CrappyDB(db_file)
    db.put(Result(url="https://image.com/a.jpeg", hashstr="abc"))
    db.put(Result(url="https://example.com/b.png", hashstr="def"))
    db.put(Result(url="http://images.bing.com/extra-1800.png", hashstr="xxx"))
    queries = [
        "https://google.com/logo.jpg",
        "ab.jpeg",
        "bc.jpeg",
        f"{tmp_path}/ab.jpeg",
        str(sub_dir),
    ]
    # WHEN
    got = list(_urls_or_files(queries, db))
    # THEN
    expected = [
        "https://google.com/logo.jpg",
        "https://image.com/a.jpeg",
        "bc.jpeg",
        "https://image.com/a.jpeg",
        "http://images.bing.com/extra-1800.png",
        str(file2),
    ]
    print(got)
    print(expected)
    assert got == expected
