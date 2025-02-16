from collections import defaultdict
from pathlib import Path

from similar_images.types import Result


def to_bit_str(s: str) -> str:
    return format(int(s, 16), "0>64b")


def hash_distance(hash1: str, hash2: str) -> bool:
    bits1 = to_bit_str(hash1)
    bits2 = to_bit_str(hash2)
    return sum([int(b1 != b2) for b1, b2 in zip(bits1, bits2)])


def near_duplicate_hash(
    hashes1: dict[str, str], hashes2: dict[str, str], max_distance: int = 2
) -> bool:
    common_keys = set(hashes1.keys()).intersection(set(hashes2.keys()))
    return any(
        hash_distance(hashes1[k], hashes2[k]) <= max_distance for k in common_keys
    )


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
        self.build_cache()

    def put(self, r: Result) -> None:
        with open(self.filename, "at") as f:
            f.write(f"{r.dump()}\n")
        self._cache.append(r)
        for field in INDEX_FIELDS:
            self._index[field][getattr(r, field)] = r

    def get(self, field: str, value: str) -> Result | None:
        return self._index.get(field, {}).get(value, None)

    def find_near_duplicate(self, hashes: dict[str, str]) -> Result | None:
        for r in self._cache:
            if r.hashes is not None:
                if near_duplicate_hash(r.hashes, hashes):
                    return r
        return None

    def scan(self):
        for r in self._cache:
            yield r

    def scan_file(self):
        with open(self.filename, "rt") as f:
            for line in f.readlines():
                r = Result.model_validate_json(line)
                yield r

    def build_cache(self) -> None:
        for r in self.scan_file():
            self._cache.append(r)
            for field in INDEX_FIELDS:
                self._index[field][getattr(r, field)] = r
