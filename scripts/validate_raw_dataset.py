"""Validate the schema and basic quality of the synthetic raw FAQ dataset."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "customer_support_synthetic.csv"
REQUIRED_COLUMNS = {
    "document_id",
    "category",
    "intent",
    "question",
    "answer",
    "data_origin",
}


def validate_dataset(input_path: Path) -> dict[str, object]:
    """Return measured dataset statistics or raise for a quality violation."""
    with input_path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
        rows = list(reader)

    if not rows:
        raise ValueError("Dataset contains no records")

    empty_fields = [
        (row_number, field)
        for row_number, row in enumerate(rows, start=2)
        for field in REQUIRED_COLUMNS
        if not (row.get(field) or "").strip()
    ]
    if empty_fields:
        raise ValueError(f"Empty required fields found: {empty_fields[:5]}")

    ids = [row["document_id"].strip() for row in rows]
    questions = [row["question"].strip().casefold() for row in rows]
    intents = [row["intent"].strip().casefold() for row in rows]
    origins = {row["data_origin"].strip().casefold() for row in rows}
    duplicate_ids = len(ids) - len(set(ids))
    duplicate_questions = len(questions) - len(set(questions))
    duplicate_intents = len(intents) - len(set(intents))

    if duplicate_ids or duplicate_questions or duplicate_intents:
        raise ValueError(
            "Duplicate values found: "
            f"ids={duplicate_ids}, questions={duplicate_questions}, intents={duplicate_intents}"
        )
    if origins != {"synthetic"}:
        raise ValueError(f"Unexpected data_origin values: {sorted(origins)}")

    category_counts = Counter(row["category"].strip() for row in rows)
    return {
        "rows": len(rows),
        "categories": len(category_counts),
        "category_counts": dict(sorted(category_counts.items())),
        "duplicate_ids": duplicate_ids,
        "duplicate_questions": duplicate_questions,
        "duplicate_intents": duplicate_intents,
        "empty_required_fields": len(empty_fields),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    stats = validate_dataset(args.input)
    print(f"Rows: {stats['rows']}")
    print(f"Categories: {stats['categories']}")
    print(f"Category counts: {stats['category_counts']}")
    print(f"Duplicate IDs: {stats['duplicate_ids']}")
    print(f"Duplicate questions: {stats['duplicate_questions']}")
    print(f"Duplicate intents: {stats['duplicate_intents']}")
    print(f"Empty required fields: {stats['empty_required_fields']}")


if __name__ == "__main__":
    main()
