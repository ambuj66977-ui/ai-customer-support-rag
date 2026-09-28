"""End-to-end retrieval-augmented answer pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from src.llm import LanguageModel
from src.prompt import build_messages
from src.retriever import FaissRetriever, RetrievalResult


FALLBACK_ANSWER = "I don't have enough information in the support knowledge base to answer that."


@dataclass(frozen=True)
class RAGResult:
    question: str
    answer: str
    retrieved_documents: list[RetrievalResult]
    used_fallback: bool


class RAGPipeline:
    def __init__(
        self,
        retriever: FaissRetriever,
        llm: LanguageModel,
        *,
        top_k: int = 3,
        min_similarity: float = 0.35,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.top_k = top_k
        self.min_similarity = min_similarity

    def ask(self, question: str) -> RAGResult:
        if not question.strip():
            raise ValueError("Question cannot be empty")
        results = self.retriever.search(
            question,
            top_k=self.top_k,
            min_similarity=self.min_similarity,
        )
        if not results:
            return RAGResult(question, FALLBACK_ANSWER, [], True)
        answer = self.llm.generate(build_messages(question, results))
        return RAGResult(question, answer or FALLBACK_ANSWER, results, not bool(answer))
