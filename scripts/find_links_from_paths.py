import json
import os

import fire

from similar_images.crappy_db import CrappyDB


def get_url(db: CrappyDB, path: str) -> str | None:
    _, file = os.path.split(path)
    name, _ = os.path.splitext(file)
    for record in db.scan():
        if record.hashstr.startswith(name):
            return record.url
    return None


def find_links_from_paths(db_path: str, paths: str) -> None:
    db = CrappyDB(db_path)
    urls = []
    for path in paths.split(","):
        if os.path.isfile(path):
            if url := get_url(db, path):
                urls.append(url)
        elif os.path.isdir(path):
            for file in os.listdir(path):
                subpath = os.path.join(path, file)
                if os.path.isfile(subpath):
                    if url := get_url(db, file):
                        urls.append(url)
    print(json.dumps(urls))


if __name__ == "__main__":
    fire.Fire(find_links_from_paths)
