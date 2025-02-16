import asyncio
import base64
import io
import json
import logging
import os
from typing import Any

import httpx
from PIL import Image
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Decision(BaseModel):
    image_path: str
    content: dict[str, Any]
    decision: str | None
    status_code: int

    def answer(self):
        logger.debug(self)
        d: str = self.decision
        if (idx := d.find("```json")) != -1:
            d = d[idx:].removeprefix("```json")
        if (idx := d.rfind("```")) != -1:
            d = d[:idx]
        d = d.strip().removesuffix(".")
        if d.isalpha() or d == "PROHIBITED_CONTENT":
            return d
        answer = json.loads(d)
        for key in ("all", "overall", "all_satisfied", "all_criteria_satisfied"):
            if key in answer:
                return answer[key].strip()
        raise Exception(f"Failed to get answer on: {self}")


class Gemini:
    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        model: str,
        max_output_tokens: int = 500,
        tries: int = 5,
        retry_sleep: float = 10,
        api_key: str | None = None,
    ):
        self._api_key = api_key if api_key else os.environ["GEMINI_API_KEY"]
        self._httpx_client = httpx_client
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._tries = tries
        self._retry_sleep = retry_sleep

    async def chat(
        self,
        query: str,
        image_paths: list[str] | None = None,
        image_contents: list[bytes] | None = None,
    ) -> Decision:
        image_paths = image_paths if image_paths else []
        image_contents = image_contents if image_contents else []
        for i in range(self._tries):
            try:
                return await self.do_chat(query, image_paths, image_contents)
            except httpx.HTTPStatusError as ex:
                logger.warning(f"Gemini failed {i=} on {image_paths=}: {type(ex)} {ex}")
                if ex.response.status_code in (429, 503, 504):
                    await asyncio.sleep(self._retry_sleep)
        image_path = image_paths[0] if image_paths else ""
        return Decision(
            image_path=image_path, content={}, decision=None, status_code=400
        )

    async def do_chat(
        self, query: str, image_paths: list[str], image_contents: list[bytes]
    ) -> Decision:
        parts = [{"text": query}]
        for image_path in image_paths:
            with open(image_path, "rb") as f:
                extension = image_path.rsplit(".")[-1]
                d = {
                    "inline_data": {
                        "mime_type": f"image/{extension.lower()}",
                        "data": base64.b64encode(f.read()).decode("ascii"),
                    }
                }
                parts.append(d)
        for content in image_contents:
            img = Image.open(io.BytesIO(content))
            d = {
                "inline_data": {
                    "mime_type": f"image/{img.format}",
                    "data": base64.b64encode(content).decode("ascii"),
                }
            }
            parts.append(d)
        data = {
            "generationConfig": {"max_output_tokens": self._max_output_tokens},
            "contents": {"parts": parts},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"
        # logger.debug(f"Gemini: {url=} {query=} {len(str(data))=}")
        response = await self._httpx_client.post(url, json=data)
        response.raise_for_status()
        image_path = image_paths[0] if image_paths else ""
        return self.parse_response(image_path, response)

    def parse_response(self, image_path: str, response: httpx.Response) -> Decision:
        content = response.json()
        decision = None
        try:
            decision = content["promptFeedback"]["blockReason"]
        except KeyError:
            pass
        try:
            decision = (
                content["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
            )
        except (KeyError, IndexError):
            pass
        return Decision(
            image_path=image_path,
            content=content,
            decision=decision,
            status_code=response.status_code,
        )
