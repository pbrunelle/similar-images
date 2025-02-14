
from similar_images.gemini import Gemini
import httpx
import fire
import os

async def run_gemini(query: str, image_paths: str):
    client = httpx.AsyncClient(follow_redirects=False, timeout=30)
    gemini = Gemini(httpx_client=client)
    decisions = []
    if os.path.isdir(image_paths):
        files = [os.path.join(image_paths, f) for f in os.listdir(image_paths) if os.path.isfile(os.path.join(image_paths, f))]
    else:
        files = image_paths.split(",")
    print(files)
    for image_path in files:
        print(image_path)
        response = await gemini.chat(query, [image_path])
        try:
            decision = response["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
        except KeyError:
            try:
                decision = response["promptFeedback"]["blockReason"]
            except KeyError:
                decision = "<error>"
        decisions.append((image_path, decision))
    for image_path, decision in decisions:
        print(f"{decision.ljust(20)} {image_path}")


if __name__ == "__main__":
    fire.Fire(run_gemini)