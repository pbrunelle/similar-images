import hashlib

from similar_images.crappy_db import CrappyDB
from similar_images.filters.filter import Filter, FilterResult, FilterStage
from similar_images.types import Result


class DbFilter(Filter):
    def __init__(self, db: CrappyDB) -> None:
        self._db = db

    def _return_result(self, record: Result) -> FilterResult:
        if not record:
            return FilterResult(keep=True)
        else:
            return FilterResult(keep=False, explanation=f"{record}")


class DbUrlFilter(DbFilter):
    """
    def __init__(self, db: CrappyDB) -> None:
        super(self).__init__(db)
    """

    def stage(self) -> FilterStage:
        return "url"

    def stat_name(self) -> str:
        return "dup_url"

    def filter(self, url: str, **kwargs) -> FilterResult:
        record = self._db.get("url", url)
        return self._return_result(record)


class DbExactDupFilter(DbFilter):
    def stage(self) -> FilterStage:
        return "contents"

    def stat_name(self) -> str:
        return "dup_hashstr"

    def filter(self, contents: bytes, **kwargs) -> FilterResult:
        hashstr = hashlib.sha256(contents).hexdigest()
        record = self._db.get("hashstr", hashstr)
        return self._return_result(record)


class DbNearDupFilter(DbFilter):
    def stage(self) -> FilterStage:
        return "hashes"

    def stat_name(self) -> str:
        return "dup_near"

    def filter(self, hashes: dict[str, str], **kwargs) -> FilterResult:
        record = self._db.find_near_duplicate(hashes)
        return self._return_result(record)
