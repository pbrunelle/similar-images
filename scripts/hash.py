from os import listdir
from os.path import isfile, join
from pathlib import Path

import fire
import imagehash
from PIL import Image


def info(directory: str):
    kept = []
    for file in listdir(directory):
        path = join(directory, file)
        if not isfile(path):
            continue
        try:
            with Image.open(path) as im:
                ahash = imagehash.average_hash(im)
                phash = imagehash.phash(im)
                dhash = imagehash.dhash(im)
                dhashv = imagehash.dhash_vertical(im)
                whash = imagehash.whash(im)
                chash = imagehash.colorhash(im)
                crhash = imagehash.crop_resistant_hash(im)
                print(
                    f"{str(ahash)}  {phash}  {dhash}  {dhashv}  {whash}  {chash}  {crhash}  {path}"
                )
                kept.append((file, ahash, phash, dhash, dhashv, whash, chash, crhash))
                # print(f"{str(ahash)}  {path}")
                # kept.append((file, ahash))
        except Exception as e:
            print(f"{path}: {type(e)} {e}")
    acmps = []
    for i, v in enumerate(kept):
        for j, w in enumerate(kept[i + 1 :]):
            diffs = [str(int(v[k] - w[k])) for k in range(1, len(v))]
            out = [v[0], w[0]] + diffs
            acmps.append((diffs[-1], join(directory, v[0]), join(directory, w[0])))
            print("  ".join(out))
    acmps = sorted(acmps, key=lambda x: int(x[00]))
    for i, acmp in enumerate(acmps[:30]):
        print(f"{i} {acmp}")


if __name__ == "__main__":
    fire.Fire(info)
