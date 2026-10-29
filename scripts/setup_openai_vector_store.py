"""Create the hosted OpenAI vector store used by the Vercel application.

Run this once after setting OPENAI_API_KEY. The script creates one small file
per canonical FAQ, with all ten customer phrasings grouped beside the single
approved answer. It prints the OPENAI_VECTOR_STORE_ID to add to Vercel.
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from openai import OpenAI, OpenAIError
from dotenv import load_dotenv, set_key

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_synthetic_dataset import build_records


def render_faq_file(records: list[dict[str, str]]) -> str:
    canonical = next(row for row in records if row["variant_style"] == "canonical")
    questions = "\n".join(f"- {row['question']}" for row in records)
    return (
        f"FAQ ID: {canonical['canonical_document_id']}\n"
        f"Category: {canonical['category']}\n"
        f"Intent: {canonical['intent']}\n\n"
        f"Canonical question: {canonical['question']}\n\n"
        f"Approved customer phrasings:\n{questions}\n\n"
        f"Approved answer:\n{canonical['answer']}\n"
    )


def main() -> None:
    # Both locations are ignored by Git. Loading the web file makes the setup
    # command and the Vercel-compatible local app share one secret location.
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(PROJECT_ROOT / "web" / ".env.local")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set. Add it to web/.env.local before running this script."
        )

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in build_records():
        grouped[record["canonical_document_id"]].append(record)

    client = OpenAI()
    vector_store = client.vector_stores.create(name="Northstar Support Knowledge Base")

    with tempfile.TemporaryDirectory(prefix="northstar-openai-kb-") as directory:
        paths: list[Path] = []
        for canonical_id, records in sorted(grouped.items()):
            path = Path(directory) / f"{canonical_id}.md"
            path.write_text(render_faq_file(records), encoding="utf-8")
            paths.append(path)

        handles = [path.open("rb") for path in paths]
        try:
            batch = client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=handles,
                chunking_strategy={
                    "type": "static",
                    "static": {"max_chunk_size_tokens": 4096, "chunk_overlap_tokens": 0},
                },
            )
        finally:
            for handle in handles:
                handle.close()

    status = getattr(batch, "status", "unknown")
    if status != "completed" or batch.file_counts.failed:
        raise RuntimeError(f"Vector-store upload finished with status {status!r}")

    print("OpenAI knowledge base is ready.")
    print(f"Uploaded canonical FAQs: {len(grouped)}")
    print(f"OPENAI_VECTOR_STORE_ID={vector_store.id}")
    private_env = PROJECT_ROOT / "web" / ".env.local"
    set_key(private_env, "OPENAI_VECTOR_STORE_ID", vector_store.id)
    private_env.chmod(0o600)
    print("Saved the vector-store ID in the private web/.env.local file.")


if __name__ == "__main__":
    try:
        main()
    except OpenAIError as error:
        # Authentication errors can contain a fragment of the submitted key.
        # Keep setup logs useful without printing credential-bearing messages.
        status = getattr(error, "status_code", None)
        print(f"OpenAI setup failed: {type(error).__name__} (HTTP {status}).", file=sys.stderr)
        raise SystemExit(1) from None
