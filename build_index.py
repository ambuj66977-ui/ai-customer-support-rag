"""Build the persisted FAISS index from processed FAQ documents."""

from src.config import settings
from src.embeddings import SentenceTransformerEmbedder
from src.vector_store import build_index, load_processed_documents


def main() -> None:
    documents = load_processed_documents(settings.processed_data_path)
    embedder = SentenceTransformerEmbedder(settings.embedding_model)
    manifest = build_index(
        documents=documents,
        embedder=embedder,
        output_directory=settings.index_directory,
        embedding_model_name=settings.embedding_model,
    )
    print(
        f"Built {manifest.index_type} with {manifest.document_count} documents, "
        f"dimension {manifest.dimension}, using {manifest.embedding_model}."
    )


if __name__ == "__main__":
    main()
