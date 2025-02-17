import os
from typing import Generator

from similar_images.crappy_db import CrappyDB


def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def get_url_from_db(path: str, db: CrappyDB | None) -> str | None:
    if not db:
        return None
    _, file = os.path.split(path)
    name, _ = os.path.splitext(file)
    for r in db.scan():
        if r.hashstr.startswith(name):
            return r.url
    return None


def get_urls_or_files(
    paths: list[str], db: CrappyDB | None = None
) -> Generator[str, None, None]:
    """From a list of URLs, directories and files, produce a list of URLs and files.

    Prefer URLs to files: if a file is known to `db` (using its name as a hash prefix),
    use the URL instead.
    Expand directories into files, but don't recursively expand sub-directories."""
    for p in paths:
        if is_url(p):
            yield p
        elif os.path.isfile(p):
            url = get_url_from_db(p, db)
            yield url or os.path.abspath(p)
        elif os.path.isdir(p):
            for file in os.listdir(p):
                path = os.path.join(p, file)
                if os.path.isfile(path):
                    url = get_url_from_db(path, db)
                    yield url or os.path.abspath(path)
