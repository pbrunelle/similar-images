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
    content: dict[str, Any]  # response.json()
    block: str | None  # response.json()["promptFeedback"]["blockReason"]
    text: str | None  # response.json()["candidates"][0]["content"]["parts"][0]["text"]
    decision: str | None  # either block or text.strip().lower()
    status_code: int  # response.status_code
    usage: dict[str, int] | None  # response.json()["usageMetadata"]

    def answer(self):
        d: str = self.decision
        if (idx := d.find("```json")) != -1:
            d = d[idx:].removeprefix("```json")
        if (idx := d.rfind("```")) != -1:
            d = d[:idx]
        d = d.strip().removesuffix(".")
        try:
            answer = json.loads(d)
            for key in (
                "answer",
                "all",
                "overall",
                "all_satisfied",
                "all_criteria_satisfied",
            ):
                if key in answer:
                    return answer[key].strip()
        except json.JSONDecodeError as e:
            pass
        return d


class Gemini:
    def __init__(
        self,
        httpx_client: httpx.AsyncClient,
        model: str,
        max_output_tokens: int = 500,
        tries: int = 5,
        retry_sleep: float = 10,
        api_key: str | None = None,
        text_before_image: bool = True,
    ):
        self._api_key = api_key if api_key else os.environ["GEMINI_API_KEY"]
        self._httpx_client = httpx_client
        self._model = model
        self._max_output_tokens = max_output_tokens
        self._tries = tries
        self._retry_sleep = retry_sleep
        self._text_before_image = text_before_image

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
        parts = []
        if self._text_before_image:
            parts.append({"text": query})
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
        if not self._text_before_image:
            parts.append({"text": query})
        data = {
            "generationConfig": {
                "max_output_tokens": self._max_output_tokens,
            },
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
        block = content.get("promptFeedback", {}).get("blockReason", None)
        decision = block
        usage = content.get("usageMetadata")
        usage = dict(
            (k, v)
            for k, v in usage.items()
            if k in ("promptTokenCount", "candidatesTokenCount", "totalTokenCount")
        )
        try:
            text = content["candidates"][0]["content"]["parts"][0]["text"]
            decision = text.strip().lower()
        except (KeyError, IndexError):
            text = None

        return Decision(
            image_path=image_path,
            content=content,
            block=block,
            text=text,
            decision=decision,
            status_code=response.status_code,
            usage=usage,
        )
