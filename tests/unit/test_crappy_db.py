import pytest

from similar_images.crappy_db import CrappyDB
from similar_images.types import Result


def test_crappy_db_new(tmp_path):
    # GIVEN
    db_file = tmp_path / "test_crappy_db_new.jsonl"
    # WHEN
    db = CrappyDB(db_file)
    # THEN
    assert not list(db.scan())
    assert not db.get("url", "https://image.com/a.jpeg")


def test_crappy_db_add(tmp_path):
    # GIVEN
    db_file = tmp_path / "test_crappy_db_add.jsonl"
    db = CrappyDB(db_file)
    r1 = Result(url="https://image.com/a.jpeg", hashstr="abc")
    r2 = Result(url="https://example.com/b.png", hashstr="def")
    r3 = Result(url="http://images.bing.com/extra-1800.png", hashstr="xxx")
    # WHEN
    db.put(r1)
    db.put(r2)
    db.put(r3)
    # THEN
    assert list(db.scan()) == [r1, r2, r3]
    assert db.get("url", "https://image.com/a.jpeg") == r1
    assert db.get("url", "http://images.bing.com/extra-1800.png") == r3
    assert not db.get("url", "https://image.com/b.jpeg")
    assert db.get("hashstr", "abc") == r1
    assert db.get("hashstr", "def") == r2
    assert not db.get("hashstr", "yyy")


def test_crappy_db_existing(tmp_path):
    # GIVEN
    db_file = tmp_path / "test_crappy_db_existing.jsonl"
    db1 = CrappyDB(db_file)
    r1 = Result(url="https://image.com/a.jpeg", hashstr="abc")
    r2 = Result(url="https://example.com/b.png", hashstr="def")
    r3 = Result(url="http://images.bing.com/extra-1800.png", hashstr="xxx")
    db1.put(r1)
    db1.put(r2)
    db2 = CrappyDB(db_file)
    # WHEN
    db2.put(r3)
    # THEN
    assert list(db2.scan()) == [r1, r2, r3]
    assert db2.get("url", "https://image.com/a.jpeg") == r1
    assert db2.get("url", "http://images.bing.com/extra-1800.png") == r3
    assert not db2.get("url", "https://image.com/b.jpeg")
    assert db2.get("hashstr", "abc") == r1
    assert db2.get("hashstr", "def") == r2
    assert not db2.get("hashstr", "yyy")
