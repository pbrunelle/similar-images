import datetime
import os
from io import BytesIO
from unittest.mock import AsyncMock, Mock, call, patch

import httpx
import pytest
from PIL import Image

from similar_images.crappy_db import CrappyDB
from similar_images.filters.db_filters import (
    DbExactDupFilter,
    DbNearDupFilter,
    DbUrlFilter,
)
from similar_images.filters.image_filters import ImageFilter
from similar_images.scraper import Scraper, _apply_filters
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


async def search_fn(query: str, max_images: int = -1):
    match query:
        case "hello":
            for i in range(3):
                yield f"http://images.com/{i}.png"
        case "world":
            pass  # no images
        case "!":
            yield f"http://images.com/1.png"
            for i in range(2):
                yield f"http://google.com/images/img{i}.jpeg"
        case _:
            raise Exception(f"search_fn: unexpected query: {query}")


async def download(url: str) -> bytes:
    img = None
    match url:
        case "http://images.com/0.png":
            img = Image.new(mode="RGB", size=(10, 10))
        case "http://images.com/1.png":
            img = Image.new(mode="RGB", size=(500, 500))
        case "http://images.com/2.png":
            img = Image.new(mode="RGB", size=(500, 500))
        case "http://google.com/images/img0.jpeg":
            img = Image.new(mode="RGB", size=(501, 501))
        case "http://google.com/images/img1.jpeg":
            img = Image.radial_gradient(mode="L")
    if not img:
        raise Exception(f"download: unexpected url: {url}")
    contents = BytesIO()
    extension = url.split(".")[-1]
    img.save(contents, format=extension)
    contents.seek(0)
    return httpx.Response(
        status_code=200,
        content=contents.read(),
        request=httpx.Request(method="GET", url=url),
    )


@patch("similar_images.scraper.datetime")
@patch("similar_images.scraper.logger")
@pytest.mark.asyncio
async def test_scrape_async(mock_logger, mock_datetime, tmp_path):
    # GIVEN
    mock_datetime.datetime.now.return_value = datetime.datetime(2010, 11, 1, 5, 6, 7)
    db_file = tmp_path / "test_scrape_async.jsonl"
    outdir = tmp_path / "out"
    debug_dir = tmp_path / "debug"
    db = CrappyDB(db_file)
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=download)
    filters = [
        DbUrlFilter(db),
        DbExactDupFilter(db),
        DbNearDupFilter(db),
        ImageFilter((100, 100), 50_000),
    ]
    scraper = Scraper(
        browser=Mock(),
        client=mock_client,
        db=db,
        filters=filters,
        debug_outdir=str(debug_dir),
    )
    queries = ["hello", "world", "!"]
    # WHEN
    links = await scraper.scrape_async(
        queries=queries, outdir=outdir, count=10, search_fn=search_fn
    )
    # THEN
    expected_links = [
        # small - http://images.com/0.png
        f"{outdir}/c53d298c.png",  # http://images.com/1.png"
        # dup:hash - http://images.com/2.png
        # dup:url - http://images.com/1.png
        # dup:near - http://google.com/images/img0.jpeg
        f"{outdir}/c3d592d9.jpeg",  # http://google.com/images/img1.jpeg
    ]
    assert links == set(expected_links)
    assert set(os.listdir(outdir)) == {"c53d298c.png", "c3d592d9.jpeg"}
    expected_info_calls = [
        call(
            "Done query='hello' | links:3 | dup:url:0 dup:hash:1 small:1 dup:near:0 err:0 | new:1"
        ),
        call(
            "Cumulative n=1 | links:3 | dup:url:0 dup:hash:1 small:1 dup:near:0 err:0 | new:1"
        ),
        call(
            "Done query='world' | links:0 | dup:url:0 dup:hash:0 small:0 dup:near:0 err:0 | new:0"
        ),
        call(
            "Cumulative n=2 | links:3 | dup:url:0 dup:hash:1 small:1 dup:near:0 err:0 | new:1"
        ),
        call(
            "Done query='!' | links:3 | dup:url:1 dup:hash:0 small:0 dup:near:1 err:0 | new:1"
        ),
        call(
            "Cumulative n=3 | links:6 | dup:url:1 dup:hash:1 small:1 dup:near:1 err:0 | new:2"
        ),
    ]
    match = Result(
        url="http://images.com/1.png",
        hashstr="c53d298c7ee5f8d06af64b68c06f93245a165397549a8d55aeecbad16743a689",
        ts=mock_datetime.datetime.now.return_value,
        path=f"{tmp_path}/out/c53d298c.png",
        query="hello",
        hashes={
            "a": "0000000000000000",
            "p": "0000000000000000",
            "d": "0000000000000000",
            "dv": "0000000000000000",
            "w": "0000000000000000",
        },
    )
    assert mock_logger.info.call_args_list == expected_info_calls
    expected_debug_calls = [
        call("Too small: http://images.com/0.png: (10, 10)"),
        call(f"Downloaded http://images.com/1.png to {tmp_path}/out/c53d298c.png"),
        call(f"Already downloaded (dup:hash): http://images.com/2.png: ({match})"),
        call(f"Already downloaded (dup:url): http://images.com/1.png: ({match})"),
        call(
            f"Already downloaded (dup:near): http://google.com/images/img0.jpeg: ({match})"
        ),
        call(
            f"Dumped http://google.com/images/img0.jpeg to {tmp_path}/debug/dup:near/3ce1635b.jpeg"
        ),
        call(
            f"Downloaded http://google.com/images/img1.jpeg to {tmp_path}/out/c3d592d9.jpeg"
        ),
    ]
    assert mock_logger.debug.call_args_list == expected_debug_calls
