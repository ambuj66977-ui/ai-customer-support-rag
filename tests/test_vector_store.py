from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.vector_store import build_index, load_index
from tests.fakes import FakeEmbedder


class VectorStoreTests(unittest.TestCase):
    def test_index_round_trip_preserves_document_mapping(self) -> None:
        documents = [
            {"document_id": "FAQ-1", "retrieval_text": "alpha", "document_text": "full alpha"},
            {"document_id": "FAQ-2", "retrieval_text": "beta", "document_text": "full beta"},
        ]
        embedder = FakeEmbedder({"alpha": [1.0, 0.0], "beta": [0.0, 1.0]})

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            manifest = build_index(documents, embedder, path, "fake-model")
            index, loaded_documents, loaded_manifest = load_index(path)

        self.assertEqual(index.ntotal, 2)
        self.assertEqual(loaded_documents, documents)
        self.assertEqual(manifest, loaded_manifest)
        self.assertEqual(manifest.similarity, "cosine_similarity_via_normalized_inner_product")
