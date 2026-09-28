from __future__ import annotations

import unittest

import faiss
import numpy as np

from src.evaluate import evaluate_retriever
from src.retriever import FaissRetriever
from src.vector_store import IndexManifest
from tests.fakes import FakeEmbedder


class RetrievalEvaluationTests(unittest.TestCase):
    def test_metrics_use_expected_document_ids_and_threshold(self) -> None:
        documents = [
            {"document_id": "FAQ-1", "question": "One", "answer": "A", "category": "x", "intent": "one"},
            {"document_id": "FAQ-2", "question": "Two", "answer": "B", "category": "x", "intent": "two"},
        ]
        index = faiss.IndexFlatIP(2)
        index.add(np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32))
        embedder = FakeEmbedder(
            {
                "first": [0.9, 0.1],
                "second": [0.1, 0.9],
                "outside": [0.2, 0.2],
            }
        )
        retriever = FaissRetriever(index, documents, IndexManifest("fake", 2, 2), embedder)
        queries = [
            {"query_id": "Q1", "query": "first", "expected_document_id": "FAQ-1", "query_type": "in_domain"},
            {"query_id": "Q2", "query": "second", "expected_document_id": "FAQ-2", "query_type": "in_domain"},
            {"query_id": "Q3", "query": "outside", "expected_document_id": "", "query_type": "out_of_domain"},
        ]

        metrics, details = evaluate_retriever(retriever, queries, min_similarity=0.3)

        self.assertEqual(metrics.recall_at_1, 1.0)
        self.assertEqual(metrics.recall_at_3, 1.0)
        self.assertEqual(metrics.out_of_domain_rejection_rate, 1.0)
        self.assertTrue(details[-1]["rejected_by_threshold"])
