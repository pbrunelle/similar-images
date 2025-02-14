from pathlib import Path

from similar_images.types import Result


class CrappyDB:
    def __init__(self, filename: str):
        self.filename = filename
        Path(filename).touch()

    def put(self, r: Result) -> None:
        with open(self.filename, "at") as f:
            f.write(f"{r.dump()}\n")

    def get(self, field: str, value: str) -> Result | None:
        with open(self.filename, "rt") as f:
            for line in f:
                r = Result.model_validate_json(line)
                if getattr(r, field) == value:
                    return r
        return None
