"""Grounded customer-support prompt construction."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from src.retriever import RetrievalResult


SYSTEM_INSTRUCTION = """You are a customer-support assistant for the fictional Northstar Shop.
Answer using only facts in the supplied support context.
Select the source that most directly answers the customer's question and copy or faithfully paraphrase its approved answer.
If the context is insufficient, say: "I don't have enough information in the support knowledge base to answer that."
Do not invent policies, steps, prices, dates, or contact details.
Keep the response concise and helpful."""

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_INSTRUCTION),
        (
            "human",
            "Support context:\n{context}\n\nCustomer question:\n{question}\n\nAnswer:",
        ),
    ]
)


def format_context(results: list[RetrievalResult]) -> str:
    """Format retrieved FAQs as clearly separated, attributable context."""
    return "\n\n".join(
        (
            f"[Source {result.document_id}]\n"
            f"Question: {result.question}\n"
            f"Answer: {result.answer}\n"
            f"Category: {result.category}"
        )
        for result in results
    )


def build_messages(question: str, results: list[RetrievalResult]):
    """Render LangChain messages for the configured chat model."""
    return RAG_PROMPT.format_messages(question=question, context=format_context(results))
