from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_synthetic_dataset import build_records, write_dataset
from scripts.validate_raw_dataset import validate_dataset


class SyntheticDatasetTests(unittest.TestCase):
    def test_web_query_catalog_matches_canonical_titles_and_contains_no_answers(self) -> None:
        catalog_path = Path(__file__).resolve().parents[1] / "web" / "lib" / "faq-catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        expected = [
            {"id": row["canonical_document_id"], "category": row["category"], "question": row["question"]}
            for row in build_records()
            if row["variant_style"] == "canonical"
        ]
        self.assertEqual(catalog, expected)

    def test_catalog_has_expected_shape_and_unique_values(self) -> None:
        records = build_records()

        self.assertEqual(len(records), 2_000)
        self.assertEqual(len({row["document_id"] for row in records}), 2_000)
        self.assertEqual(len({row["question"].casefold() for row in records}), 2_000)
        self.assertEqual(len({row["intent"].casefold() for row in records}), 2_000)
        self.assertEqual(len({row["canonical_document_id"] for row in records}), 200)
        self.assertEqual(len({row["variant_style"] for row in records}), 10)
        self.assertEqual({row["data_origin"] for row in records}, {"synthetic"})

    def test_generated_csv_passes_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pilot.csv"
            write_dataset(output)

            stats = validate_dataset(output)

        self.assertEqual(stats["rows"], 2_000)
        self.assertEqual(stats["canonical_records"], 200)
        self.assertEqual(stats["categories"], 20)
        self.assertEqual(set(stats["category_counts"].values()), {100})

    def test_generator_protects_existing_raw_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "pilot.csv"
            write_dataset(output)

            with self.assertRaises(FileExistsError):
                write_dataset(output)


if __name__ == "__main__":
    unittest.main()
