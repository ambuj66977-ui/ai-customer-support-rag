"""Clean raw FAQ records and build documents for later embedding."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "customer_support_synthetic.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "faq_documents.csv"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "processed" / "preprocessing_report.json"

REQUIRED_COLUMNS = {
    "document_id",
    "category",
    "intent",
    "question",
    "answer",
    "data_origin",
}
OUTPUT_COLUMNS = [
    "document_id",
    "category",
    "intent",
    "question",
    "answer",
    "retrieval_text",
    "document_text",
    "data_origin",
]
MIN_QUESTION_LENGTH = 8
MIN_ANSWER_LENGTH = 15
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class PreprocessingStats:
    """Measured counts from one preprocessing run."""

    input_rows: int
    retained_rows: int
    removed_rows: int
    removed_missing_required: int
    removed_short_question: int
    removed_short_answer: int
    removed_exact_duplicates: int
    categories: int
    category_counts: dict[str, int]


def normalize_text(value: str | None) -> str:
    """Normalize Unicode and collapse all runs of whitespace."""
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKC", value)
    return WHITESPACE_PATTERN.sub(" ", normalized).strip()


def build_document_text(question: str, answer: str, category: str) -> str:
    """Create the text that the embedding model will receive."""
    return f"Question: {question}\n\nAnswer: {answer}\n\nCategory: {category}"


def _normalize_row(row: dict[str, str | None]) -> dict[str, str]:
    return {column: normalize_text(row.get(column)) for column in REQUIRED_COLUMNS}


def preprocess_rows(
    rows: Iterable[dict[str, str | None]],
) -> tuple[list[dict[str, str]], PreprocessingStats]:
    """Normalize, validate, deduplicate, and convert raw rows to documents.

    Exact repeated question/answer pairs are removed. Repeated normalized
    questions with different answers are rejected because silently choosing one
    would make the support knowledge base internally inconsistent.
    """
    input_rows = 0
    counters: Counter[str] = Counter()
    processed: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    answer_by_question: dict[str, str] = {}

    for source_row_number, raw_row in enumerate(rows, start=2):
        input_rows += 1
        row = _normalize_row(raw_row)

        if any(not row[column] for column in REQUIRED_COLUMNS):
            counters["missing_required"] += 1
            continue
        if len(row["question"]) < MIN_QUESTION_LENGTH:
            counters["short_question"] += 1
            continue
        if len(row["answer"]) < MIN_ANSWER_LENGTH:
            counters["short_answer"] += 1
            continue

        document_id_key = row["document_id"].casefold()
        if document_id_key in seen_ids:
            raise ValueError(
                f"Duplicate document_id {row['document_id']!r} at CSV row {source_row_number}"
            )

        question_key = row["question"].casefold()
        answer_key = row["answer"].casefold()
        previous_answer = answer_by_question.get(question_key)
        if previous_answer is not None:
            if previous_answer == answer_key:
                counters["exact_duplicates"] += 1
                continue
            raise ValueError(
                f"Conflicting answers for normalized question {row['question']!r} "
                f"at CSV row {source_row_number}"
            )

        seen_ids.add(document_id_key)
        answer_by_question[question_key] = answer_key
        processed.append(
            {
                **row,
                "retrieval_text": row["question"],
                "document_text": build_document_text(
                    question=row["question"],
                    answer=row["answer"],
                    category=row["category"],
                ),
            }
        )

    category_counts = Counter(row["category"] for row in processed)
    retained_rows = len(processed)
    stats = PreprocessingStats(
        input_rows=input_rows,
        retained_rows=retained_rows,
        removed_rows=input_rows - retained_rows,
        removed_missing_required=counters["missing_required"],
        removed_short_question=counters["short_question"],
        removed_short_answer=counters["short_answer"],
        removed_exact_duplicates=counters["exact_duplicates"],
        categories=len(category_counts),
        category_counts=dict(sorted(category_counts.items())),
    )
    return processed, stats


def load_raw_csv(input_path: Path) -> list[dict[str, str | None]]:
    """Load a raw CSV after checking that its declared schema is usable."""
    with input_path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
        return list(reader)


def write_processed_csv(records: list[dict[str, str]], output_path: Path) -> None:
    """Write the reproducible processed dataset."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def write_report(stats: PreprocessingStats, report_path: Path) -> None:
    """Write measured preprocessing statistics as machine-readable JSON."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as file:
        json.dump(asdict(stats), file, indent=2, sort_keys=True)
        file.write("\n")


def run_preprocessing(
    input_path: Path = DEFAULT_INPUT,
    output_path: Path = DEFAULT_OUTPUT,
    report_path: Path = DEFAULT_REPORT,
) -> PreprocessingStats:
    """Run the complete deterministic preprocessing operation."""
    raw_rows = load_raw_csv(input_path)
    records, stats = preprocess_rows(raw_rows)
    write_processed_csv(records, output_path)
    write_report(stats, report_path)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    stats = run_preprocessing(args.input, args.output, args.report)
    print(json.dumps(asdict(stats), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
