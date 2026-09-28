"""Build, persist, and load the FAISS cosine-similarity index."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import faiss

from src.embeddings import Embedder


INDEX_FILENAME = "index.faiss"
DOCUMENTS_FILENAME = "documents.json"
MANIFEST_FILENAME = "manifest.json"


@dataclass(frozen=True)
class IndexManifest:
    embedding_model: str
    dimension: int
    document_count: int
    embedding_field: str = "retrieval_text"
    index_type: str = "IndexFlatIP"
    similarity: str = "cosine_similarity_via_normalized_inner_product"


def load_processed_documents(path: Path) -> list[dict[str, str]]:
    """Load processed records and ensure embedding text is present."""
    with path.open(encoding="utf-8", newline="") as file:
        records = list(csv.DictReader(file))
    if not records:
        raise ValueError(f"No processed documents found in {path}")
    required = {
        "document_id",
        "question",
        "answer",
        "category",
        "intent",
        "retrieval_text",
        "document_text",
    }
    missing = required - set(records[0])
    if missing:
        raise ValueError(f"Processed dataset is missing columns: {sorted(missing)}")
    if any(not record["retrieval_text"].strip() for record in records):
        raise ValueError("Processed dataset contains an empty retrieval_text")
    return records


def build_index(
    documents: list[dict[str, str]],
    embedder: Embedder,
    output_directory: Path,
    embedding_model_name: str,
) -> IndexManifest:
    """Embed documents and persist an exact normalized inner-product index."""
    texts = [document["retrieval_text"] for document in documents]
    vectors = embedder.embed_documents(texts)
    if vectors.shape != (len(documents), embedder.dimension):
        raise ValueError(
            f"Unexpected embedding shape {vectors.shape}; "
            f"expected {(len(documents), embedder.dimension)}"
        )

    index = faiss.IndexFlatIP(embedder.dimension)
    index.add(vectors)
    manifest = IndexManifest(
        embedding_model=embedding_model_name,
        dimension=embedder.dimension,
        document_count=len(documents),
    )

    output_directory.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output_directory / INDEX_FILENAME))
    (output_directory / DOCUMENTS_FILENAME).write_text(
        json.dumps(documents, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_directory / MANIFEST_FILENAME).write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_index(directory: Path) -> tuple[faiss.Index, list[dict[str, str]], IndexManifest]:
    """Load persisted index artifacts and verify their mapping."""
    index = faiss.read_index(str(directory / INDEX_FILENAME))
    documents = json.loads((directory / DOCUMENTS_FILENAME).read_text(encoding="utf-8"))
    manifest = IndexManifest(**json.loads((directory / MANIFEST_FILENAME).read_text(encoding="utf-8")))
    if index.ntotal != len(documents) or index.ntotal != manifest.document_count:
        raise ValueError("FAISS index, document mapping, and manifest counts do not match")
    if index.d != manifest.dimension:
        raise ValueError("FAISS dimension does not match the manifest")
    return index, documents, manifest
