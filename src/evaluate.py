"""Evaluate retrieval recall and out-of-domain threshold behavior."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from src.config import PROJECT_ROOT, settings
from src.embeddings import SentenceTransformerEmbedder
from src.retriever import FaissRetriever


DEFAULT_RESULTS_DIRECTORY = PROJECT_ROOT / "evaluation" / "results"


@dataclass(frozen=True)
class RetrievalMetrics:
    in_domain_queries: int
    out_of_domain_queries: int
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    mean_reciprocal_rank_at_5: float
    out_of_domain_rejection_rate: float
    min_similarity: float


def load_evaluation_queries(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    required = {"query_id", "query", "expected_document_id", "query_type"}
    if not rows or required - set(rows[0]):
        raise ValueError("Evaluation CSV is empty or has an invalid schema")
    for row in rows:
        if row["query_type"] not in {"in_domain", "out_of_domain"}:
            raise ValueError(f"Invalid query_type for {row['query_id']}")
        if row["query_type"] == "in_domain" and not row["expected_document_id"]:
            raise ValueError(f"Missing expected document for {row['query_id']}")
    return rows


def evaluate_retriever(
    retriever: FaissRetriever,
    queries: list[dict[str, str]],
    *,
    min_similarity: float,
) -> tuple[RetrievalMetrics, list[dict[str, str | float | int | bool]]]:
    details: list[dict[str, str | float | int | bool]] = []
    hits = {1: 0, 3: 0, 5: 0}
    reciprocal_rank_sum = 0.0
    in_domain_count = 0
    out_of_domain_count = 0
    rejected_out_of_domain = 0

    for row in queries:
        unfiltered = retriever.search(row["query"], top_k=5)
        ids = [result.document_id for result in unfiltered]
        top_similarity = unfiltered[0].similarity if unfiltered else -1.0
        expected = row["expected_document_id"]
        expected_rank = ids.index(expected) + 1 if expected in ids else 0

        if row["query_type"] == "in_domain":
            in_domain_count += 1
            for k in hits:
                hits[k] += int(expected in ids[:k])
            if expected_rank:
                reciprocal_rank_sum += 1.0 / expected_rank
        else:
            out_of_domain_count += 1
            rejected_out_of_domain += int(top_similarity < min_similarity)

        details.append(
            {
                "query_id": row["query_id"],
                "query": row["query"],
                "query_type": row["query_type"],
                "expected_document_id": expected,
                "expected_rank": expected_rank,
                "top_document_id": ids[0] if ids else "",
                "top_similarity": round(top_similarity, 6),
                "retrieved_ids": "|".join(ids),
                "rejected_by_threshold": top_similarity < min_similarity,
            }
        )

    metrics = RetrievalMetrics(
        in_domain_queries=in_domain_count,
        out_of_domain_queries=out_of_domain_count,
        recall_at_1=hits[1] / in_domain_count,
        recall_at_3=hits[3] / in_domain_count,
        recall_at_5=hits[5] / in_domain_count,
        mean_reciprocal_rank_at_5=reciprocal_rank_sum / in_domain_count,
        out_of_domain_rejection_rate=(
            rejected_out_of_domain / out_of_domain_count if out_of_domain_count else 0.0
        ),
        min_similarity=min_similarity,
    )
    return metrics, details


def write_results(
    metrics: RetrievalMetrics,
    details: list[dict[str, str | float | int | bool]],
    directory: Path,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "retrieval_metrics.json").write_text(
        json.dumps(asdict(metrics), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (directory / "retrieval_details.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=details[0].keys())
        writer.writeheader()
        writer.writerows(details)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=Path, default=settings.evaluation_path)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULTS_DIRECTORY)
    parser.add_argument("--min-similarity", type=float, default=settings.min_similarity)
    args = parser.parse_args()

    embedder = SentenceTransformerEmbedder(settings.embedding_model)
    retriever = FaissRetriever.from_directory(settings.index_directory, embedder)
    queries = load_evaluation_queries(args.queries)
    metrics, details = evaluate_retriever(
        retriever, queries, min_similarity=args.min_similarity
    )
    write_results(metrics, details, args.output)
    print(json.dumps(asdict(metrics), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
