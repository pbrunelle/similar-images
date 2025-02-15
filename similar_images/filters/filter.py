from pydantic import BaseModel
from typing import Literal



class FilterResult(BaseModel):
    keep: bool
    explanation: str | None = None

type FilterStage = Literal["url", "contents", "hashes", "image"]

class Filter:

    def stage(self) -> FilterStage:
        raise NotImplementedError()
        
    def stat_name(self) -> str:
        raise NotImplementedError()

    def filter(self, *args, **kwargs) -> FilterResult:
        raise NotImplementedError()