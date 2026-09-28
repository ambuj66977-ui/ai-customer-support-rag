"""End-to-end retrieval-augmented answer pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from src.llm import LanguageModel
from src.prompt import build_messages
from src.retriever import FaissRetriever, RetrievalResult


FALLBACK_ANSWER = "I don't have enough information in the support knowledge base to answer that."
PROMPT_LEAKAGE_MARKERS = (
    "you are a customer-support assistant",
    "select the source that most directly answers",
    "if the context is insufficient",
    "do not invent policies",
)


def _looks_like_prompt_leak(answer: str) -> bool:
    """Detect copied internal instructions before they reach the interface."""
    normalized = " ".join(answer.lower().split())
    return any(marker in normalized for marker in PROMPT_LEAKAGE_MARKERS)


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
        answer_from_top_source: bool = False,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.answer_from_top_source = answer_from_top_source

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
        if self.answer_from_top_source:
            return RAGResult(question, results[0].answer, results, False)
        answer = self.llm.generate(build_messages(question, results)).strip()
        if not answer or _looks_like_prompt_leak(answer):
            # Retrieval already passed the similarity gate. Returning the
            # top-ranked approved FAQ is safer than exposing prompt text.
            answer = results[0].answer
        return RAGResult(question, answer, results, False)
