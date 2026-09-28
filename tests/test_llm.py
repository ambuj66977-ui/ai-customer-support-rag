from __future__ import annotations

import unittest

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import (
    LLMConfigurationError,
    OpenAILanguageModel,
    _build_local_prompt,
    create_language_model,
)


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

    def test_local_prompt_excludes_internal_system_instruction(self) -> None:
        prompt = _build_local_prompt(
            [
                SystemMessage(content="SECRET SYSTEM INSTRUCTION"),
                HumanMessage(content="Support context: Return within 30 days.\nQuestion: Returns?"),
            ]
        )

        self.assertNotIn("SECRET SYSTEM INSTRUCTION", prompt)
        self.assertIn("Return within 30 days", prompt)
        self.assertTrue(prompt.endswith("FINAL ANSWER:"))
