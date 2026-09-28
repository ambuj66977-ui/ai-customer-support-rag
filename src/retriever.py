"""Semantic retrieval over the persisted FAISS index."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np

from src.embeddings import Embedder
from src.vector_store import IndexManifest, load_index


@dataclass(frozen=True)
class RetrievalResult:
    document_id: str
    question: str
    answer: str
    category: str
    intent: str
    similarity: float
    rank: int


class FaissRetriever:
    """Search normalized embeddings with exact cosine similarity."""

    def __init__(
        self,
        index: faiss.Index,
        documents: list[dict[str, str]],
        manifest: IndexManifest,
        embedder: Embedder,
    ) -> None:
        if embedder.dimension != manifest.dimension:
            raise ValueError(
                f"Embedder dimension {embedder.dimension} does not match "
                f"index dimension {manifest.dimension}"
            )
        self.index = index
        self.documents = documents
        self.manifest = manifest
        self.embedder = embedder

    @classmethod
    def from_directory(cls, directory: Path, embedder: Embedder) -> "FaissRetriever":
        index, documents, manifest = load_index(directory)
        embedder_name = getattr(embedder, "model_name", None)
        if embedder_name is not None and embedder_name != manifest.embedding_model:
            raise ValueError(
                f"Embedder model {embedder_name!r} does not match indexed model "
                f"{manifest.embedding_model!r}"
            )
        return cls(index, documents, manifest, embedder)

    def search(
        self,
        query: str,
        *,
        top_k: int = 3,
        min_similarity: float | None = None,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        query_vector = np.asarray(self.embedder.embed_query(query), dtype=np.float32).reshape(1, -1)
        if query_vector.shape[1] != self.manifest.dimension:
            raise ValueError("Query embedding dimension does not match the index")

        result_count = min(top_k, len(self.documents))
        similarities, positions = self.index.search(query_vector, result_count)
        results: list[RetrievalResult] = []
        for rank, (position, similarity) in enumerate(
            zip(positions[0], similarities[0], strict=True), start=1
        ):
            if position < 0:
                continue
            score = float(similarity)
            if min_similarity is not None and score < min_similarity:
                continue
            document = self.documents[int(position)]
            results.append(
                RetrievalResult(
                    document_id=document["document_id"],
                    question=document["question"],
                    answer=document["answer"],
                    category=document["category"],
                    intent=document["intent"],
                    similarity=score,
                    rank=rank,
                )
            )
        return results
