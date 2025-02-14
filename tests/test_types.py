from datetime import datetime

import pytest

from similar_images.types import Result


@pytest.mark.parametrize(
    "result,expected",
    [
        (
            Result(
                url="http",
                hashstr="abcdef",
                ts=datetime(2000, 10, 5, 12, 13, 14),
                path="/here/i/am",
                query="cats and dogs",
                hashes={"a": "abc", "p": "def"},
            ),
            '{"url":"http","hashstr":"abcdef","ts":"2000-10-05T12:13:14","query":"cats and dogs","hashes":{"a":"abc","p":"def"}}',
        ),
        (
            Result(url="http", hashstr="abcdef"),
            '{"url":"http","hashstr":"abcdef"}',
        ),
    ],
)
def test_write(result, expected):
    assert result.dump() == expected


@pytest.mark.parametrize(
    "s,expected",
    [
        (
            '{"url":"http","hashstr":"abcdef","ts":"2000-10-05T12:13:14","path":"/here/i/am","query":"cats and dogs","hashes":{"a":"abc","p":"def"}}',
            Result(
                url="http",
                hashstr="abcdef",
                ts=datetime(2000, 10, 5, 12, 13, 14),
                path="/here/i/am",
                query="cats and dogs",
                hashes={"a": "abc", "p": "def"},
            ),
        ),
        (
            '{"url":"http","hashstr":"abcdef"}',
            Result(url="http", hashstr="abcdef"),
        ),
    ],
)
def test_read(s, expected):
    assert Result.model_validate_json(s) == expected
