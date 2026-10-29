export function contentText(content = []) {
  return content
    .filter((part) => part && part.type === "text" && typeof part.text === "string")
    .map((part) => part.text)
    .join("\n");
}

export function field(text, label, nextLabel) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const end = nextLabel
    ? `(?=\\n+${nextLabel.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}:)`
    : "(?![\\s\\S])";
  return text.match(new RegExp(`(?:^|\\n)${escaped}:[ \\t]*\\n?([\\s\\S]*?)${end}`))?.[1]?.trim() || "";
}

export function parseSearchResult(result) {
  const text = contentText(result.content);
  const answer = field(text, "Approved answer");
  // A partial search chunk is never safe to display as an approved answer.
  if (!answer) return null;
  return {
    documentId: field(text, "FAQ ID", "Category") || result.filename?.replace(/\.md$/i, "") || "FAQ",
    category: field(text, "Category", "Intent") || "support",
    question: field(text, "Canonical question", "Approved customer phrasings") || "Supporting FAQ",
    answer,
    similarity: Number(result.score || 0),
  };
}
