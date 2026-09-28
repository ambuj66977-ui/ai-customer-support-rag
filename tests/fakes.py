from __future__ import annotations

from collections.abc import Sequence

import numpy as np


class FakeEmbedder:
    """Small deterministic embedder for tests; vectors are already normalized."""

    def __init__(self, vectors: dict[str, list[float]], dimension: int = 2) -> None:
        self.vectors = vectors
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        return np.asarray([self.vectors[text] for text in texts], dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(self.vectors[text], dtype=np.float32)


class FakeLLM:
    def __init__(self, answer: str = "Generated from context.") -> None:
        self.answer = answer
        self.messages = None

    def generate(self, messages):
        self.messages = messages
        return self.answer
