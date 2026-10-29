import assert from "node:assert/strict";
import test from "node:test";

import { parseSearchResult } from "./sources.js";

test("parses a hosted vector search result into a UI source", () => {
  const source = parseSearchResult({
    filename: "FAQ-0001.md",
    score: 0.81,
    content: [{
      type: "text",
      text: "FAQ ID: FAQ-0001\nCategory: account\nIntent: create_account\n\nCanonical question: How do I create an account?\n\nApproved customer phrasings:\n- How do I create an account?\n\nApproved answer:\nChoose Create account and verify your email.\n",
    }],
  });

  assert.deepEqual(source, {
    documentId: "FAQ-0001",
    category: "account",
    question: "How do I create an account?",
    answer: "Choose Create account and verify your email.",
    similarity: 0.81,
  });
});

test("preserves a complete multiline approved answer", () => {
  const source = parseSearchResult({
    filename: "FAQ-0002.md",
    score: 0.9,
    content: [{ type: "text", text: "FAQ ID: FAQ-0002\nCategory: returns\nIntent: return_item\n\nCanonical question: How do I return an item?\n\nApproved customer phrasings:\n- Return an item\n\nApproved answer:\nOpen Order history.\nSelect Return and follow the instructions.\n" }],
  });
  assert.equal(source.answer, "Open Order history.\nSelect Return and follow the instructions.");
});

test("rejects chunks without an approved answer instead of displaying prompt context", () => {
  assert.equal(parseSearchResult({
    filename: "FAQ-0002.md",
    content: [{ type: "text", text: "FAQ ID: FAQ-0002\nApproved customer phrasings:\n- How do I return?" }],
  }), null);
});
