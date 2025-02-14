import base64
import os
from typing import Any

import httpx
import asyncio

class Gemini:
    def __init__(self, httpx_client: httpx.AsyncClient):
        self._api_key = os.environ["GEMINI_API_KEY"]
        self._httpx_client = httpx_client

    async def do_chat(self, query: str, image_paths: list[str]) -> dict[str, Any]:
        parts = [{"text": query}]
        for image_path in image_paths:
            with open(image_path, "rb") as f:
                extension = image_path.rsplit(".")[-1]
                d = {
                    "inline_data": {
                        "mime_type": f"image/{extension}",
                        "data": base64.b64encode(f.read()).decode("ascii"),
                    }
                }
                parts.append(d)
        data = {
            "generationConfig": {"max_output_tokens": 100},
            "contents": {"parts": parts},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self._api_key}"
        response = await self._httpx_client.post(url, json=data)
        print(response)
        print(response.content)
        response.raise_for_status()
        return response.json()

    async def chat(self, query: str, image_paths: list[str]) -> dict[str, Any]:
        for _ in range(5):
            try:
                return await self.do_chat(query, image_paths)
            except httpx.HTTPStatusError as ex:
                print(f"{type(ex)} {ex}")
                asyncio.sleep(10)
        return {}