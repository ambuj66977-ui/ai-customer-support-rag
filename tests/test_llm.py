from __future__ import annotations

import unittest

from src.llm import LLMConfigurationError, OpenAILanguageModel, create_language_model


class LanguageModelConfigurationTests(unittest.TestCase):
    def test_openai_provider_requires_api_key(self) -> None:
        with self.assertRaisesRegex(LLMConfigurationError, "configuration is missing"):
            OpenAILanguageModel("example-model", None)

    def test_unknown_provider_is_rejected(self) -> None:
        with self.assertRaisesRegex(LLMConfigurationError, "Unsupported LLM_PROVIDER"):
            create_language_model(
                "unknown",
                openai_model="example-model",
                openai_api_key=None,
                local_model="example-local-model",
            )
