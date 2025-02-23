import logging

import httpx

from similar_images.filters.filter import Filter, FilterResult, FilterStage
from similar_images.gemini import Gemini

logger = logging.getLogger("__name__")


class GeminiFilter(Filter):
    def __init__(
        self,
        *args,
        query: str,
        keep_responses: list[str],
        model: str,
        timeout: float = 10,
        filter_name: str | None = None,
        **kwargs,
    ):
        self._query = query
        self._keep_responses = keep_responses
        self._model = model
        self._httpx_client = httpx.AsyncClient(timeout=timeout)
        self._filter_name = filter_name or "llm"
        self._gemini = Gemini(
            *args,
            httpx_client=self._httpx_client,
            model=model,
            **kwargs,
        )

    def stage(self) -> FilterStage:
        return "expensive"

    def stat_name(self) -> str:
        return self._filter_name

    async def filter(self, url: str, contents: bytes, **kwargs) -> FilterResult:
        got = await self._gemini.chat(query=self._query, image_contents=[contents])
        status = got.status_code
        block = got.block
        decision = got.decision
        logger.debug(
            f"Gemini {self._model}/{self._filter_name}: {url=} {status=} {block=} {decision=}"
        )
        if got.answer() in self._keep_responses:
            return FilterResult(keep=True)
        else:
            explanation = f"Rejected by {self._model}/{self._filter_name}: {url}: {status=} {block=} {decision=}"
            return FilterResult(keep=False, explanation=explanation)
