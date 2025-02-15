
from similar_images.gemini import Gemini
import httpx
import fire
import os
import logging

logger = logging.getLogger(__name__)

async def run_gemini(query: str, image_paths: str, outfile: str, model: str = "gemini-1.5-flash", max_output_tokens: int = 100):
    logging.basicConfig(level=logging.DEBUG, force=True)
    client = httpx.AsyncClient(follow_redirects=False, timeout=30)
    gemini = Gemini(httpx_client=client, model=model, max_output_tokens=max_output_tokens)
    files = []
    for file in image_paths.split(","):
        if os.path.isfile(file):
            files.append(file)
        elif os.path.isdir(file):
            for subfile in os.listdir(file):
                subpath = os.path.join(file, subfile)
                if os.path.isfile(subpath):
                    files.append(os.path.abspath(subpath))
    logger.info(f"Processing: {len(files)}: {files}")
    for file in files:
        logger.debug(f"Processing: {file}")
        decision = await gemini.chat(query, [file])
        with open(outfile, "at") as f:
            f.write(f"{decision.model_dump_json()}\n")


if __name__ == "__main__":
    fire.Fire(run_gemini)