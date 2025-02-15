import pytest

from similar_images.crappy_db import hash_distance, near_duplicate_hash


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
