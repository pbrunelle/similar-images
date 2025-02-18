import base64
import logging
import os

import fire
import google.generativeai as genai
import httpx


def _get_mime_type(path: str) -> str:
    extension = path.split(".")[-1]
    return f"image/{extension}"


generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}


def generativeai(path: str, query: str, model: str = "gemini-1.5-flash"):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        model_name=model,
        generation_config=generation_config,
    )
    file = genai.upload_file(path, mime_type=_get_mime_type(path))
    history = [{"role": "user", "parts": [file]}]
    chat_session = model.start_chat(history=history)
    response = chat_session.send_message(query)
    print(f"generativeai: [{response.text}]")


def rest(path: str, query: str, model: str = "gemini-1.5-flash"):
    api_key = os.environ["GEMINI_API_KEY"]
    with open(path, "rb") as f:
        file = base64.b64encode(f.read()).decode("ascii")
    parts = [
        {
            "inline_data": {
                "mime_type": _get_mime_type(path),
                "data": file,
            }
        },
        {"text": query},
    ]
    data = {
        "generationConfig": generation_config,
        "contents": {"parts": parts},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    response = httpx.post(url, json=data)
    response.raise_for_status()
    block = response.json().get("promptFeedback", {}).get("blockReason")
    if block:
        print(f"rest: block [{block}]")
    else:
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        print(f"rest: text [{text}]")


def double(path: str, query: str, model: str = "gemini-1.5-flash"):
    rest(path, query, model)
    generativeai(path, query, model)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    fire.Fire(double)
