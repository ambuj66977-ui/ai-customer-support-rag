"""Central project configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _env_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be at least 1")
    return value


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    top_k: int = _env_int("TOP_K", 3)
    min_similarity: float = _env_float("MIN_SIMILARITY", 0.35)
    llm_provider: str = os.getenv("LLM_PROVIDER", "local").strip().lower()
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    local_llm_model: str = os.getenv("LOCAL_LLM_MODEL", "google/flan-t5-small")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    processed_data_path: Path = PROJECT_ROOT / "data" / "processed" / "faq_documents.csv"
    index_directory: Path = PROJECT_ROOT / "vectorstore" / "faiss_index"
    evaluation_path: Path = PROJECT_ROOT / "data" / "evaluation" / "retrieval_queries.csv"


settings = Settings()
