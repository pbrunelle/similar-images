import fire
import shutil
from pathlib import Path

def move(decision_file: str, outdir: str) -> None:
    with open(decision_file, "rt") as f:
        for line in f:
            decision, src = line.split()
            dst = f"{outdir}/{decision}"
            Path(dst).mkdir(parents=True, exist_ok=True)
            shutil.move(src, dst)

if __name__ == "__main__":
    fire.Fire(move)