from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from src.summarize_response_evaluation import summarize


class ResponseSummaryTests(unittest.TestCase):
    def test_summary_calculates_scores_by_query_type(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            responses = root / "responses.csv"
            scores = root / "scores.csv"
            with responses.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["query_id", "query_type"])
                writer.writeheader()
                writer.writerows(
                    [
                        {"query_id": "Q1", "query_type": "in_domain"},
                        {"query_id": "Q2", "query_type": "out_of_domain"},
                    ]
                )
            with scores.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=["query_id", *(
                        "relevance_0_to_2",
                        "groundedness_0_to_2",
                        "fallback_correct_0_to_2",
                    )],
                )
                writer.writeheader()
                writer.writerows(
                    [
                        {"query_id": "Q1", "relevance_0_to_2": 2, "groundedness_0_to_2": 1, "fallback_correct_0_to_2": 2},
                        {"query_id": "Q2", "relevance_0_to_2": 0, "groundedness_0_to_2": 1, "fallback_correct_0_to_2": 0},
                    ]
                )

            result = summarize(responses, scores)

        self.assertEqual(result["overall"]["relevance_0_to_2_mean"], 1.0)
        self.assertEqual(result["overall"]["groundedness_0_to_2_percent_of_max"], 50.0)
        self.assertEqual(result["in_domain"]["queries"], 1)
