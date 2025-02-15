from collections import defaultdict

import fire

from similar_images.gemini import Decision


def decisions(decision_file: str) -> None:
    d = defaultdict(int)
    with open(decision_file, "rt") as f:
        for line in f:
            decision = Decision.model_validate_json(line)
            answer = decision.answer()
            d[answer] += 1
    print(dict(d))


if __name__ == "__main__":
    fire.Fire(decisions)
