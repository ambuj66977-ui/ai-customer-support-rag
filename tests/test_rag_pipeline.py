from __future__ import annotations

import unittest

from src.rag_pipeline import FALLBACK_ANSWER, RAGPipeline
from src.retriever import RetrievalResult
from tests.fakes import FakeLLM


class StubRetriever:
    def __init__(self, results):
        self.results = results
        self.arguments = None

    def search(self, question, *, top_k, min_similarity):
        self.arguments = (question, top_k, min_similarity)
        return self.results


class RAGPipelineTests(unittest.TestCase):
    def test_no_retrieval_uses_fallback_without_calling_llm(self) -> None:
        retriever = StubRetriever([])
        llm = FakeLLM()
        pipeline = RAGPipeline(retriever, llm)

        result = pipeline.ask("Unanswerable question")

        self.assertEqual(result.answer, FALLBACK_ANSWER)
        self.assertTrue(result.used_fallback)
        self.assertIsNone(llm.messages)

    def test_retrieved_context_is_passed_to_llm(self) -> None:
        source = RetrievalResult("FAQ-1", "How?", "Do this.", "account", "how", 0.8, 1)
        retriever = StubRetriever([source])
        llm = FakeLLM("Helpful answer")
        pipeline = RAGPipeline(retriever, llm, top_k=1, min_similarity=0.4)

        result = pipeline.ask("Please help")

        self.assertEqual(result.answer, "Helpful answer")
        self.assertFalse(result.used_fallback)
        rendered = "\n".join(str(message.content) for message in llm.messages)
        self.assertIn("Do this.", rendered)
        self.assertIn("Please help", rendered)
        self.assertEqual(retriever.arguments, ("Please help", 1, 0.4))

    def test_prompt_leak_is_replaced_with_top_approved_answer(self) -> None:
        source = RetrievalResult(
            "FAQ-1",
            "What is your return policy?",
            "Return eligible items within 30 days.",
            "returns",
            "return_policy",
            0.8,
            1,
        )
        retriever = StubRetriever([source])
        llm = FakeLLM(
            "You are a customer-support assistant. Select the source that most directly answers."
        )

        result = RAGPipeline(retriever, llm).ask("What is your return policy?")

        self.assertEqual(result.answer, "Return eligible items within 30 days.")
        self.assertFalse(result.used_fallback)
