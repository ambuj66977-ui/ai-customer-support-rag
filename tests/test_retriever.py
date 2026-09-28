from __future__ import annotations

import unittest

import faiss
import numpy as np

from src.retriever import FaissRetriever
from src.vector_store import IndexManifest
from tests.fakes import FakeEmbedder


class RetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents = [
            {"document_id": "FAQ-1", "question": "Alpha?", "answer": "A", "category": "one", "intent": "alpha"},
            {"document_id": "FAQ-2", "question": "Beta?", "answer": "B", "category": "two", "intent": "beta"},
        ]
        index = faiss.IndexFlatIP(2)
        index.add(np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32))
        embedder = FakeEmbedder({"alpha query": [0.9, 0.1], "weak": [0.2, 0.1]})
        manifest = IndexManifest("fake", 2, 2)
        self.retriever = FaissRetriever(index, self.documents, manifest, embedder)

    def test_search_returns_ranked_document_and_similarity(self) -> None:
        results = self.retriever.search("alpha query", top_k=2)

        self.assertEqual([result.document_id for result in results], ["FAQ-1", "FAQ-2"])
        self.assertEqual([result.rank for result in results], [1, 2])
        self.assertAlmostEqual(results[0].similarity, 0.9, places=5)

    def test_threshold_removes_weak_results(self) -> None:
        self.assertEqual(self.retriever.search("weak", top_k=2, min_similarity=0.3), [])

    def test_empty_query_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.retriever.search("  ")
