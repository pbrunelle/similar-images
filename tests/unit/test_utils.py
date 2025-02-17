import os
from pathlib import Path

from similar_images.crappy_db import CrappyDB
from similar_images.types import Result
from similar_images.utils import get_urls_or_files


def test_urls_or_files(tmp_path):
    # GIVEN
    os.chdir(tmp_path)
    db_file = tmp_path / "test_urls_or_files.jsonl"
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir(parents=True, exist_ok=True)
    for path in [
        Path(sub_dir / "xxx.png"),
        Path(sub_dir / "xyz.png"),
        Path("ab.jpeg"),
        Path("mno.jpeg"),
    ]:
        path.touch()
    db = CrappyDB(db_file)
    for result in [
        Result(url="https://image.com/a.jpeg", hashstr="abc"),
        Result(url="https://example.com/b.png", hashstr="def"),
        Result(url="http://images.bing.com/extra-1800.png", hashstr="xxx"),
    ]:
        db.put(result)
    queries = [
        "https://google.com/logo.jpg",
        "ab.jpeg",
        "bc.jpeg",
        f"{tmp_path}/ab.jpeg",
        str(sub_dir),
        "mno.jpeg",
    ]
    # WHEN
    got = list(get_urls_or_files(queries, db))
    # THEN
    expected = [
        "https://google.com/logo.jpg",  # https://google.com/logo.jpg - already URL
        "https://image.com/a.jpeg",  # ab.jpeg - basename 'ab' is prefix of hashstr 'abc'
        # bc.jpeg - not a URL, no hashstr match, and file does not exist
        "https://image.com/a.jpeg",  # /tmp/.../ab.jpeg - basename 'ab' is prefix of hashstr 'abc'
        "http://images.bing.com/extra-1800.png",  # /tmp/.../sub/ -> xxx.png - matches hashstr 'xxx'
        str(
            sub_dir / "xyz.png"
        ),  # /tmp/.../sub/ -> xyz.png - not URL nor hash match but file exists
        str(tmp_path / "mno.jpeg"),  # mno.jpeg - not URL nor hash match but file exists
    ]
    assert got == expected
