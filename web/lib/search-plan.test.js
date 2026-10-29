import assert from "node:assert/strict";
import test from "node:test";

import { planSearch } from "./search-plan.js";

test("canonical questions use their own search title without a model call", async () => {
  assert.deepEqual(await planSearch({}, "HOW LONG DO I HAVE TO RETURN AN ITEM", "test"), {
    canonicalId: "FAQ-0081",
    query: "How long do I have to return an item?",
  });
});

test("query planning can only select known FAQ titles", async () => {
  const fake = { responses: { create: async () => ({ output_text: '{"canonicalId":"FAQ-0081"}' }) } };
  const plan = await planSearch(fake, "What is your return policy?", "test");
  assert.equal(plan.canonicalId, "FAQ-0081");
  assert.equal(plan.query, "How long do I have to return an item?");
});

test("unrelated questions and unrecognized IDs cannot be retrieved as valid FAQs", async () => {
  for (const canonicalId of ["", "invented-faq"]) {
    const fake = { responses: { create: async () => ({ output_text: JSON.stringify({ canonicalId }) }) } };
    assert.equal(await planSearch(fake, "Tell me tomorrow's weather", "test"), null);
  }
});
