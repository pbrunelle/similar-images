from collections import defaultdict
from pathlib import Path

from similar_images.types import Result

INDEX_FIELDS = ["url", "hashstr"]


class CrappyDB:
    """CrappyDB assumes a single process and a single thread accesses the storage file at a time."""

    def __init__(self, filename: str):
        self.filename = filename
        Path(filename).touch()
        self._cache: list[Result] = []
        self._index: dict[str, dict[str, Result]] = defaultdict(
            dict
        )  # field name -> field value -> result
        self._build_cache()

    def put(self, r: Result) -> None:
        with open(self.filename, "at") as f:
            f.write(f"{r.dump()}\n")
        self._cache.append(r)
        for field in INDEX_FIELDS:
            self._index[field][getattr(r, field)] = r

    def get(self, field: str, value: str) -> Result | None:
        return self._index.get(field, {}).get(value, None)

    def scan(self):
        for r in self._cache:
            yield r

    def _scan_file(self):
        with open(self.filename, "rt") as f:
            for line in f.readlines():
                r = Result.model_validate_json(line)
                yield r

    def _build_cache(self) -> None:
        for r in self._scan_file():
            self._cache.append(r)
            for field in INDEX_FIELDS:
                self._index[field][getattr(r, field)] = r
