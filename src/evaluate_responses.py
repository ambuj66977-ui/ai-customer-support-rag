"""Generate answers for a manual relevance, groundedness, and fallback review."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.config import PROJECT_ROOT, settings
from src.embeddings import SentenceTransformerEmbedder
from src.llm import create_language_model
from src.rag_pipeline import RAGPipeline
from src.retriever import FaissRetriever


DEFAULT_QUERIES = PROJECT_ROOT / "data" / "evaluation" / "response_queries.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "evaluation" / "results" / "response_evaluation.csv"
OUTPUT_COLUMNS = [
    "query_id",
    "query",
    "query_type",
    "answer",
    "retrieved_document_ids",
    "retrieved_context",
    "used_fallback",
    "relevance_0_to_2",
    "groundedness_0_to_2",
    "fallback_correct_0_to_2",
    "reviewer_notes",
]


def generate_response_review_file(input_path: Path, output_path: Path) -> None:
    """Call the configured LLM and create a CSV ready for honest manual scoring."""
    with input_path.open(encoding="utf-8", newline="") as file:
        queries = list(csv.DictReader(file))
    if not queries:
        raise ValueError("Response evaluation query set is empty")

    embedder = SentenceTransformerEmbedder(settings.embedding_model)
    retriever = FaissRetriever.from_directory(settings.index_directory, embedder)
    llm = create_language_model(
        settings.llm_provider,
        openai_model=settings.llm_model,
        openai_api_key=settings.openai_api_key,
        local_model=settings.local_llm_model,
    )
    pipeline = RAGPipeline(
        retriever,
        llm,
        top_k=settings.top_k,
        min_similarity=settings.min_similarity,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for query in queries:
            result = pipeline.ask(query["query"])
            writer.writerow(
                {
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "query_type": query["query_type"],
                    "answer": result.answer,
                    "retrieved_document_ids": "|".join(
                        source.document_id for source in result.retrieved_documents
                    ),
                    "retrieved_context": "\n\n".join(
                        f"[{source.document_id}] {source.question}\n{source.answer}"
                        for source in result.retrieved_documents
                    ),
                    "used_fallback": result.used_fallback,
                    "relevance_0_to_2": "",
                    "groundedness_0_to_2": "",
                    "fallback_correct_0_to_2": "",
                    "reviewer_notes": "",
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generate_response_review_file(args.queries, args.output)
    print(f"Wrote unscored manual response review to {args.output}")


if __name__ == "__main__":
    main()
