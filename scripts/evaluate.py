import json
from datetime import datetime

import fire
import httpx

from similar_images.gemini import Gemini
from similar_images.utils import get_files



async def evaluate_dataset(
    gemini: Gemini, query: str, files: list[str], positive_answers: list[str]
) -> tuple[int, int]:
    # Return number of True and False answers
    P, N = 0, 0
    for file in files:
        # print(f"{file=}")
        decision = await gemini.chat(query, image_paths=[file])
        print(f"Processed {file}: {decision} {decision.answer()}")
        if decision.answer() in positive_answers:
            P += 1
        else:
            N += 1
    return P, N


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
):
    client = httpx.AsyncClient(follow_redirects=False, timeout=30)
    gemini = Gemini(
        httpx_client=client, model=model, max_output_tokens=max_output_tokens
    )
    expected = positive_answers.split()
    positive_files = get_files(positive_paths.split(","))
    negative_files = get_files(negative_paths.split(","))
    TP, FN = await evaluate_dataset(gemini, query, positive_files, expected)
    FP, TN = await evaluate_dataset(gemini, query, negative_files, expected)
    pr, rec = get_precision_recall(TP, FP, TN, FN)
    d = {
        "precision": pr,
        "recall": rec,
        "TP": TP,
        "FP": FP,
        "TN": TN,
        "FN": FN,
        "P": len(positive_files),
        "N": len(negative_files),
        "model": model,
        "query": query,
        "time": str(datetime.now()),
        "positive_paths": positive_paths,
        "negative_paths": negative_paths,
    }
    print(json.dumps(d))


if __name__ == "__main__":
    fire.Fire(evaluate)
