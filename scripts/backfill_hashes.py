from PIL import Image
import imagehash
import fire
from pathlib import Path
from os import listdir
from os.path import isfile, join
from similar_images.crappy_db import CrappyDB
import asyncio
import httpx
import io

async def download(client, url):
    try:
        response = await client.get(url)
        response.raise_for_status()
        contents = response.content
        return (url, contents)
    except Exception as e:
        return (url, None)

async def process_batch(batch, output_db):
    client = httpx.AsyncClient(follow_redirects=True, timeout=30)
    tasks = [download(client, record.url) for record in batch if not record.hashes]
    results = await asyncio.gather(*tasks)
    url2contents = dict(results)
    for record in batch:
        try:
            if contents := url2contents.get(record.url):
                img = Image.open(io.BytesIO(contents))
                hashes = {
                    "a": str(imagehash.average_hash(img)),
                    "p": str(imagehash.phash(img)),
                    "d": str(imagehash.dhash(img)),
                    "dv": str(imagehash.dhash_vertical(img)),
                    "w": str(imagehash.whash(img)),
                }
                record.hashes = hashes
        except Exception as e:
            pass
        output_db.put(record)

def backfill(input_db_path: str, output_db_path: str, batch_size: int = 500):
    input_db = CrappyDB(input_db_path)
    output_db = CrappyDB(output_db_path)
    generator = input_db.scan()
    batch = []
    try:
        while True:
            for _ in range(batch_size):
                batch.append(next(generator))
            asyncio.run(process_batch(batch, output_db))
            batch = []
    except StopIteration:
        if batch:
            asyncio.run(process_batch(batch, output_db))

if __name__ == "__main__":
    fire.Fire(backfill)