from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.preprocessing import (
    OUTPUT_COLUMNS,
    build_document_text,
    normalize_text,
    preprocess_rows,
    run_preprocessing,
)


def valid_row(**overrides: str) -> dict[str, str]:
    row = {
        "document_id": "FAQ-0001",
        "category": "account",
        "intent": "change_email",
        "question": "How can I change my email address?",
        "answer": "Open account settings and update your registered email address.",
        "data_origin": "synthetic",
    }
    row.update(overrides)
    return row


class TextPreprocessingTests(unittest.TestCase):
    def test_normalize_text_collapses_whitespace_and_unicode_width(self) -> None:
        self.assertEqual(normalize_text("  How\n\tare   ｙｏｕ?  "), "How are you?")

    def test_document_text_has_explicit_sections(self) -> None:
        document = build_document_text("Question?", "Answer.", "account")

        self.assertEqual(
            document,
            "Question: Question?\n\nAnswer: Answer.\n\nCategory: account",
        )

    def test_invalid_and_exact_duplicate_rows_are_counted(self) -> None:
        rows = [
            valid_row(),
            valid_row(document_id="FAQ-0002"),
            valid_row(document_id="FAQ-0003", question="short"),
            valid_row(document_id="FAQ-0004", answer="too short"),
            valid_row(document_id="FAQ-0005", category=""),
        ]

        processed, stats = preprocess_rows(rows)

        self.assertEqual(len(processed), 1)
        self.assertEqual(stats.input_rows, 5)
        self.assertEqual(stats.retained_rows, 1)
        self.assertEqual(stats.removed_rows, 4)
        self.assertEqual(stats.removed_exact_duplicates, 1)
        self.assertEqual(stats.removed_short_question, 1)
        self.assertEqual(stats.removed_short_answer, 1)
        self.assertEqual(stats.removed_missing_required, 1)

    def test_conflicting_answers_for_same_question_are_rejected(self) -> None:
        rows = [
            valid_row(),
            valid_row(
                document_id="FAQ-0002",
                answer="Contact support because this answer contradicts the first one.",
            ),
        ]

        with self.assertRaisesRegex(ValueError, "Conflicting answers"):
            preprocess_rows(rows)

    def test_duplicate_document_ids_are_rejected(self) -> None:
        rows = [
            valid_row(),
            valid_row(question="Where can I update my account name?"),
        ]

        with self.assertRaisesRegex(ValueError, "Duplicate document_id"):
            preprocess_rows(rows)


class PreprocessingIntegrationTests(unittest.TestCase):
    def test_pipeline_writes_processed_csv_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "raw.csv"
            output_path = root / "processed.csv"
            report_path = root / "report.json"
            with input_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=valid_row().keys())
                writer.writeheader()
                writer.writerow(valid_row(question="  How can I\nchange my email address?  "))

            stats = run_preprocessing(input_path, output_path, report_path)

            with output_path.open(encoding="utf-8", newline="") as file:
                records = list(csv.DictReader(file))
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(stats.retained_rows, 1)
        self.assertEqual(list(records[0]), OUTPUT_COLUMNS)
        self.assertEqual(records[0]["question"], "How can I change my email address?")
        self.assertEqual(records[0]["retrieval_text"], records[0]["question"])
        self.assertIn("Question:", records[0]["document_text"])
        self.assertEqual(report["retained_rows"], 1)


if __name__ == "__main__":
    unittest.main()
