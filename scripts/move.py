import shutil
from pathlib import Path

import fire

from similar_images.gemini import Decision


def move(decision_file: str, outdir: str) -> None:
    with open(decision_file, "rt") as f:
        for line in f:
            decision = Decision.model_validate_json(line)
            subdir = decision.answer()
            dst = f"{outdir}/{subdir}"
            Path(dst).mkdir(parents=True, exist_ok=True)
            shutil.move(decision.image_path, dst)


if __name__ == "__main__":
    fire.Fire(move)
