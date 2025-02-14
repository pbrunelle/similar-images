import datetime
import logging

from pydantic import BaseModel


class CommonConfiguration(BaseModel):
    outdir: str | None = None
    database: str | None = None
    count: int | None = None
    wait_between_scroll: float | None = None
    wait_first_load: float | None = None
    headless: bool | None = None
    safe_search: bool | None = None


class RunConfiguration(CommonConfiguration):
    queries: str

    def resolve(self, common: CommonConfiguration) -> None:
        fields_to_resolve = [
            "outdir",
            "database",
            "count",
            "wait_between_scroll",
            "wait_first_load",
            "headless",
            "safe_search",
        ]
        for field in fields_to_resolve:
            if getattr(self, field) is None:
                setattr(self, field, getattr(common, field))


class ScrapeConfiguration(BaseModel):
    common: CommonConfiguration | None = None
    runs: list[RunConfiguration]
    verbosity: int | str = logging.INFO
    logfile: str = ""


class Result(BaseModel):
    url: str
    hashstr: str
    ts: datetime.datetime | None = None
    path: str | None = None
    query: str | None = None
    hashes: dict[str, str] | None = None

    def dump(self):
        return self.model_dump_json(exclude={"path"}, exclude_none=True)
