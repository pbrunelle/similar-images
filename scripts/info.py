from pathlib import Path

import fire
from PIL import Image


def info(directory: str):
    for file in Path(directory).rglob("*"):
        if file.is_file():
            try:
                with Image.open(file) as im:
                    print(f"{file}: {im.format}, {im.size}, {im.mode}, {im.getbbox()}")
            except Exception as e:
                print(f"{file}: {type(e)} {e}")


if __name__ == "__main__":
    fire.Fire(info)
