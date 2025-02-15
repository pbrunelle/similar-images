import asyncio

import httpx

from similar_images.filters.filter import Filter, FilterResult, FilterStage
from similar_images.gemini import Decision, Gemini


class GeminiFilter(Filter):
    def __init__(
        self,
        *args,
        query: str,
        keep_responses: list[str],
        model: str,
        timeout: float = 10,
        **kwargs,
    ):
        self._query = query
        self._keep_responses = keep_responses
        self._httpx_client = httpx.AsyncClient(timeout=timeout)
        self._gemini = Gemini(
            *args,
            httpx_client=self._httpx_client,
            model=model,
            **kwargs,
        )

    def stage(self) -> FilterStage:
        return "expensive"

    def stat_name(self) -> str:
        return "llm"

    async def filter(
        self, url: str, query: str, contents: bytes, **kwargs
    ) -> FilterResult:
        decision = await self._gemini.chat(query=query, image_contents=[contents])
        if decision.decision in self._keep_responses:
            return FilterResult(keep=True)
        else:
            explanation = f"Rejected by Gemini: {url}: {decision}"
            return FilterResult(keep=False, explanation=explanation)
