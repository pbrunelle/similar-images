from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from similar_images.image_sources import BrowserImageSource, LocalFileImageSource


# tmp_path
# ├── nop.jpeg
# ├── qrs.jpeg
# ├── sub
# │   ├── abc.png
# │   └── def.png
# └── sub2
#     ├── ghi.png
#     └── yep
#         └── klm.png
@pytest.fixture
def test_dir(tmp_path):
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir(parents=True, exist_ok=True)
    sub_dir2 = tmp_path / "sub2"
    sub_dir2.mkdir(parents=True, exist_ok=True)
    sub_dir3 = tmp_path / "sub2" / "yep"
    sub_dir3.mkdir(parents=True, exist_ok=True)
    for path in [
        Path(sub_dir / "abc.png"),
        Path(sub_dir / "def.png"),
        Path(sub_dir2 / "ghi.png"),
        Path(sub_dir3 / "klm.png"),
        Path(tmp_path / "nop.jpeg"),
        Path(tmp_path / "qrs.jpeg"),
    ]:
        path.touch()
    yield tmp_path


@patch("similar_images.image_sources.random")
@pytest.mark.asyncio
async def test_browser_image_source_many(mock_ramdom, test_dir):
    # GIVEN
    mock_ramdom.shuffle.side_effect = lambda x: x.reverse()
    url = "http://image.com"
    src = BrowserImageSource(
        browser=Mock(),
        urls_or_paths=[
            str(test_dir),
            str(test_dir / "sub"),
            str(test_dir / "sub2"),
            str(test_dir / "sub2" / "yep"),
            url,
        ],
    )
    # WHEN
    batches = [path async for path in src.batches()]
    # THEN
    assert batches == [
        str(test_dir / "nop.jpeg"),
        str(test_dir / "qrs.jpeg"),
        str(test_dir / "sub" / "abc.png"),
        str(test_dir / "sub" / "def.png"),
        str(test_dir / "sub2" / "ghi.png"),
        str(test_dir / "sub2" / "yep" / "klm.png"),
        url,
    ]


@patch("similar_images.image_sources.random")
@pytest.mark.asyncio
async def test_browser_image_source_randomize(mock_ramdom, test_dir):
    # GIVEN
    mock_ramdom.shuffle.side_effect = lambda x: x.reverse()
    url = "http://image.com"
    src = BrowserImageSource(
        browser=Mock(),
        urls_or_paths=[
            str(test_dir),
            str(test_dir / "sub"),
            str(test_dir / "sub2"),
            str(test_dir / "sub2" / "yep"),
            url,
        ],
        random=True,
    )
    # WHEN
    batches = [path async for path in src.batches()]
    # THEN
    assert batches == [
        url,
        str(test_dir / "sub2" / "yep" / "klm.png"),
        str(test_dir / "sub2" / "ghi.png"),
        str(test_dir / "sub" / "def.png"),
        str(test_dir / "sub" / "abc.png"),
        str(test_dir / "qrs.jpeg"),
        str(test_dir / "nop.jpeg"),
    ]


@pytest.mark.asyncio
async def test_local_file_image_source_empty(tmp_path):
    # GIVEN
    src = LocalFileImageSource([str(tmp_path)])
    # WHEN
    batches = [path async for path in src.batches()]
    paths = []
    for b in batches:
        paths += [path async for path in src.images(b)]
    # THEN
    assert batches == [str(tmp_path)]
    assert paths == []


@pytest.mark.asyncio
async def test_local_file_image_source_many(test_dir):
    # GIVEN
    src = LocalFileImageSource([str(test_dir / "sub"), str(test_dir / "sub2" / "yep")])
    # WHEN
    batches = [path async for path in src.batches()]
    paths = [[path async for path in src.images(b)] for b in batches]
    # THEN
    assert batches == [str(test_dir / "sub"), str(test_dir / "sub2" / "yep")]
    assert paths == [
        [str(test_dir / "sub" / "abc.png"), str(test_dir / "sub" / "def.png")],
        [str(test_dir / "sub2" / "yep" / "klm.png")],
    ]


@patch("similar_images.image_sources.random")
@pytest.mark.asyncio
async def test_local_file_image_source_randomize(mock_ramdom, test_dir):
    # GIVEN
    mock_ramdom.shuffle.side_effect = lambda x: x.reverse()
    src = LocalFileImageSource(
        [
            str(test_dir),
            str(test_dir / "sub"),
            str(test_dir / "sub2"),
            str(test_dir / "sub2" / "yep"),
        ],
        random=True,
    )
    # WHEN
    batches = [path async for path in src.batches()]
    paths = [[path async for path in src.images(b)] for b in batches]
    # THEN
    assert batches == [
        str(test_dir / "sub2" / "yep"),
        str(test_dir / "sub2"),
        str(test_dir / "sub"),
        str(test_dir),
    ]
    assert paths == [
        [str(test_dir / "sub2" / "yep" / "klm.png")],
        [str(test_dir / "sub2" / "ghi.png")],
        [str(test_dir / "sub" / "def.png"), str(test_dir / "sub" / "abc.png")],
        [str(test_dir / "qrs.jpeg"), str(test_dir / "nop.jpeg")],
    ]
