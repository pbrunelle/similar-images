import hashlib

from similar_images.crappy_db import CrappyDB
from similar_images.filters.filter import Filter, FilterResult, FilterStage
from similar_images.types import Result


class DbFilter(Filter):
    def __init__(self, db: CrappyDB) -> None:
        self._db = db

    def _return_result(self, url: str, record: Result) -> FilterResult:
        if not record:
            return FilterResult(keep=True)
        else:
            explanation = f"Already downloaded ({self.stat_name()}): {url}"
            if url != record.url:
                explanation += f": {record.url}"
            return FilterResult(keep=False, explanation=explanation)


class DbUrlFilter(DbFilter):
    """
    def __init__(self, db: CrappyDB) -> None:
        super(self).__init__(db)
    """

    def stage(self) -> FilterStage:
        return "url"

    def stat_name(self) -> str:
        return "dup:url"

    def allow_debug_rejected(self) -> bool:
        return False

    async def filter(self, url: str, **kwargs) -> FilterResult:
        record = self._db.get("url", url)
        return self._return_result(url, record)


class DbExactDupFilter(DbFilter):
    def stage(self) -> FilterStage:
        return "contents"

    def stat_name(self) -> str:
        return "dup:hash"

    def allow_debug_rejected(self) -> bool:
        return False

    async def filter(self, url: str, contents: bytes, **kwargs) -> FilterResult:
        # https://stackoverflow.com/a/64994148
        hashstr = hashlib.sha256(contents).hexdigest()
        record = self._db.get("hashstr", hashstr)
        return self._return_result(url, record)


def hash_distance(hash1: str, hash2: str) -> int:
    int1 = int(hash1, 16)
    int2 = int(hash2, 16)
    return bin(int1 ^ int2).count("1")


def near_duplicate_hash(
    hashes1: dict[str, str], hashes2: dict[str, str], max_distance: int = 2
) -> bool:
    common_keys = set(hashes1.keys()).intersection(set(hashes2.keys()))
    return any(
        hash_distance(hashes1[k], hashes2[k]) <= max_distance for k in common_keys
    )


class DbNearDupFilter(DbFilter):
    def stage(self) -> FilterStage:
        return "hashes"

    def stat_name(self) -> str:
        return "dup:near"

    async def filter(self, url: str, hashes: dict[str, str], **kwargs) -> FilterResult:
        record = self._find_near_duplicate(hashes)
        return self._return_result(url, record)

    def _find_near_duplicate(self, hashes: dict[str, str]) -> Result | None:
        for r in self._db.scan():
            if r.hashes is not None:
                if near_duplicate_hash(r.hashes, hashes):
                    return r
        return None
