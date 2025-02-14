
from similar_images.gemini import Gemini
import httpx
import fire

async def run_gemini(query: str, image_paths: str):
    client = httpx.AsyncClient(follow_redirects=False, timeout=30)
    gemini = Gemini(httpx_client=client)
    response = await gemini.chat(query, image_paths.split(","))
    print(response)


if __name__ == "__main__":
    fire.Fire(run_gemini)