import asyncio
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import fire
import httpx

from similar_images.gemini import Decision, Gemini
from similar_images.utils import get_urls_or_files

logger = logging.getLogger(__name__)


async def do_chat(
    semaphore: asyncio.Semaphore, gemini: Gemini, query: str, file: str
) -> Decision:
    async with semaphore:
        logger.info(f"Processing {file}")
        decision = await gemini.chat(query, image_paths=[file])
        logger.info(f"Processed {file}: {decision} {decision.answer()}")
        return decision


async def run_dataset(
    gemini: Gemini,
    query: str,
    files: list[str],
    concurrency: int,
) -> list[Decision]:
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [do_chat(semaphore, gemini, query, file) for file in files]
    results = await asyncio.gather(*tasks)
    return results


def evaluate_dataset(
    positive_decisions: list[Decision],
    negative_decisions: list[Decision],
    positive_answers: list[str],
    outdir: str | None,
) -> dict[str, Any]:
    # Return number of True and False answers
    if outdir:
        fp_dir = f"{outdir}/fp"
        fn_dir = f"{outdir}/fn"
        Path(fp_dir).mkdir(parents=True, exist_ok=True)
        Path(fn_dir).mkdir(parents=True, exist_ok=True)
    TP, FN, FP, TN = 0, 0, 0, 0
    for decision in positive_decisions:
        if decision.answer() in positive_answers:
            TP += 1
        else:
            FN += 1
            logger.info(f"False negative: {decision}")
            if outdir:
                shutil.copy2(decision.image_path, fn_dir)
    for decision in negative_decisions:
        if decision.answer() in positive_answers:
            FP += 1
            logger.info(f"False positive: {decision}")
            if outdir:
                shutil.copy2(decision.image_path, fp_dir)
        else:
            TN += 1
    pr, rec = get_precision_recall(TP, FP, TN, FN)
    d = {
        "precision": pr,
        "recall": rec,
        "TP": TP,
        "FP": FP,
        "TN": TN,
        "FN": FN,
        "P": TP + FN,
        "N": FP + TN,
    }
    return d


def get_precision_recall(TP: int, FP: int, TN: int, FN: int) -> tuple[float, float]:
    # Return precision and recall, coding like a caveman
    pr = TP / (TP + FP) if (TP + FP) else 0.0
    rec = TP / (TP + FN) if (TP + FN) else 0.0
    return (pr, rec)


async def evaluate(
    positive_paths: str,
    negative_paths: str,
    model: str,
    query: str,
    positive_answers: str = "yes",
    max_output_tokens: int = 10,
    concurrency: int = 1,
    outdir: str | None = None,
):
    logging.basicConfig(level=logging.DEBUG)
    client = httpx.AsyncClient(follow_redirects=False, timeout=30)
    gemini = Gemini(
        httpx_client=client, model=model, max_output_tokens=max_output_tokens
    )
    positive_files = get_urls_or_files(positive_paths.split(","))
    negative_files = get_urls_or_files(negative_paths.split(","))
    positive_decisions = await run_dataset(gemini, query, positive_files, concurrency)
    negative_decisions = await run_dataset(gemini, query, negative_files, concurrency)
    d = evaluate_dataset(
        positive_decisions,
        negative_decisions,
        positive_answers.split(),
        outdir,
    )
    d["model"] = model
    d["query"] = query
    d["time"] = str(datetime.now())
    d["positive_paths"] = positive_paths
    d["negative_paths"] = negative_paths
    print(json.dumps(d))


if __name__ == "__main__":
    fire.Fire(evaluate)
