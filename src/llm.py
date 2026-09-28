"""Replaceable language-model interface and OpenAI implementation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from langchain_core.messages import BaseMessage


class LLMConfigurationError(RuntimeError):
    """Raised when answer generation is requested without valid configuration."""


class LanguageModel(Protocol):
    def generate(self, messages: Sequence[BaseMessage]) -> str: ...


def _build_local_prompt(messages: Sequence[BaseMessage]) -> str:
    """Adapt chat messages for a text-to-text model without exposing system text."""
    if not messages:
        return ""
    task = str(messages[-1].content)
    return (
        f"{task}\n\n"
        "Using only the support context above, answer the customer question concisely. "
        "Output only the final customer-facing answer, without instructions or labels.\n"
        "FINAL ANSWER:"
    )


class OpenAILanguageModel:
    """LangChain OpenAI chat-model adapter."""

    def __init__(self, model: str, api_key: str | None) -> None:
        if not api_key:
            raise LLMConfigurationError(
                "OpenAI configuration is missing. Copy .env.example to .env and set OPENAI_API_KEY."
            )
        from langchain_openai import ChatOpenAI

        self._client = ChatOpenAI(model=model, api_key=api_key, temperature=0)

    def generate(self, messages: Sequence[BaseMessage]) -> str:
        response = self._client.invoke(list(messages))
        content = response.content
        if isinstance(content, str):
            return content.strip()
        return str(content).strip()


class LocalHuggingFaceLanguageModel:
    """Small local instruction model for a no-key, reproducible demo path."""

    def __init__(self, model_name: str = "google/flan-t5-small") -> None:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.model_name = model_name
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def generate(self, messages: Sequence[BaseMessage]) -> str:
        # FLAN-T5 is a text-to-text model, not a chat model. Supplying a
        # SystemMessage verbatim can make this small model copy the internal
        # instruction instead of answering the customer.
        prompt = _build_local_prompt(messages)
        if not prompt:
            return ""
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        output_tokens = self._model.generate(
            **inputs,
            max_new_tokens=96,
            do_sample=False,
            num_beams=4,
            no_repeat_ngram_size=3,
            repetition_penalty=1.05,
        )
        return self._tokenizer.decode(output_tokens[0], skip_special_tokens=True).strip()


def create_language_model(
    provider: str,
    *,
    openai_model: str,
    openai_api_key: str | None,
    local_model: str,
) -> LanguageModel:
    """Construct the configured provider without spreading provider logic."""
    normalized = provider.strip().lower()
    if normalized == "openai":
        return OpenAILanguageModel(openai_model, openai_api_key)
    if normalized == "local":
        return LocalHuggingFaceLanguageModel(local_model)
    raise LLMConfigurationError(
        f"Unsupported LLM_PROVIDER {provider!r}; expected 'local' or 'openai'."
    )
