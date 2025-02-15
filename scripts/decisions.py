from collections import defaultdict

import fire

from similar_images.gemini import Decision


def decisions(decision_file: str) -> None:
    d = defaultdict(list)
    with open(decision_file, "rt") as f:
        for line in f:
            decision = Decision.model_validate_json(line)
            answer = decision.answer()
            d[answer].append(decision)
    counts = dict((k, len(v)) for k,v in d.items())
    for answer, decisions in d.items():
        print(f'{answer} {",".join([decision.image_path for decision in decisions])}')
    print(dict(counts))


if __name__ == "__main__":
    fire.Fire(decisions)
