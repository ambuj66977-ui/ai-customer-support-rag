"""Validate manual response scores and calculate transparent aggregate metrics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.config import PROJECT_ROOT


DEFAULT_RESPONSES = PROJECT_ROOT / "evaluation" / "results" / "response_evaluation.csv"
DEFAULT_SCORES = PROJECT_ROOT / "data" / "evaluation" / "manual_response_scores.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "evaluation" / "results" / "response_metrics.json"
SCORE_FIELDS = ("relevance_0_to_2", "groundedness_0_to_2", "fallback_correct_0_to_2")


def summarize(responses_path: Path, scores_path: Path) -> dict[str, object]:
    with responses_path.open(encoding="utf-8", newline="") as file:
        responses = {row["query_id"]: row for row in csv.DictReader(file)}
    with scores_path.open(encoding="utf-8", newline="") as file:
        scores = {row["query_id"]: row for row in csv.DictReader(file)}
    if not responses or responses.keys() != scores.keys():
        raise ValueError("Response and manual-score query IDs must be non-empty and identical")

    parsed: dict[str, dict[str, int]] = {}
    for query_id, row in scores.items():
        parsed[query_id] = {}
        for field in SCORE_FIELDS:
            score = int(row[field])
            if score not in {0, 1, 2}:
                raise ValueError(f"{query_id} has invalid {field}: {score}")
            parsed[query_id][field] = score

    def group_metrics(query_ids: list[str]) -> dict[str, float | int]:
        maximum = 2 * len(query_ids)
        result: dict[str, float | int] = {"queries": len(query_ids)}
        for field in SCORE_FIELDS:
            total = sum(parsed[query_id][field] for query_id in query_ids)
            result[f"{field}_mean"] = total / len(query_ids)
            result[f"{field}_percent_of_max"] = 100.0 * total / maximum
        return result

    all_ids = list(responses)
    in_domain_ids = [q for q, row in responses.items() if row["query_type"] == "in_domain"]
    out_of_domain_ids = [q for q, row in responses.items() if row["query_type"] == "out_of_domain"]
    return {
        "model": "google/flan-t5-small",
        "rubric": "0=poor, 1=acceptable, 2=strong",
        "overall": group_metrics(all_ids),
        "in_domain": group_metrics(in_domain_ids),
        "out_of_domain": group_metrics(out_of_domain_ids),
        "review_status": "manually_scored",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses", type=Path, default=DEFAULT_RESPONSES)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    metrics = summarize(args.responses, args.scores)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
