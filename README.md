# AI Customer Support Assistant — RAG

A lightweight, interview-defensible Retrieval-Augmented Generation (RAG) application for the fictional retailer **Northstar Shop**. It retrieves relevant FAQ records with Sentence Transformer embeddings and FAISS, then supplies those records to a configurable local or OpenAI language model through a grounded LangChain prompt.

## Quick start from a fresh clone

Python 3.12 is recommended. The first setup downloads the embedding and local language models, so an internet connection is required once. After those models are cached, the default application runs locally without an API key.

```bash
git clone https://github.com/ambuj66977-ui/ai-customer-support-rag.git
cd ai-customer-support-rag
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python scripts/bootstrap_project.py
streamlit run app.py
```

On Windows PowerShell, activate the environment with:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python scripts/bootstrap_project.py
streamlit run app.py
```

Open `http://127.0.0.1:8501` if the browser does not open automatically. Run `python -m pytest -q` to verify the installation.

## Overview

This portfolio project demonstrates the complete path from raw support data to evaluated retrieval, grounded generation, and an interactive application. It deliberately keeps the architecture small enough to inspect and explain.

## Project status

The complete local architecture is implemented and works without an API key using `google/flan-t5-small`. OpenAI is an optional provider configured through an environment variable. Both retrieval and local-model response results have been measured; the deliberately weak local baseline is documented rather than presented as production quality.

## Problem statement

Customers often describe the same problem differently from an FAQ, so exact keyword search can miss useful answers. Asking an LLM directly creates another risk: it may invent support policies absent from the knowledge base. This project retrieves relevant support information first and asks the LLM to answer using only that context.

## Solution

The system embeds each approved FAQ question, searches those vectors for the closest matches to a customer query, rejects weak retrieval, and passes accepted FAQ answers to a language model as constrained context. The result includes both the generated answer and visible source records.

## Tech stack

- Python 3.12
- Sentence Transformers (`all-MiniLM-L6-v2`)
- FAISS (`IndexFlatIP`)
- LangChain prompt primitives
- Local FLAN-T5 and optional OpenAI generation
- Streamlit
- Pytest

## Architecture

```text
Raw synthetic FAQs
        ↓
Validation and preprocessing
        ↓
Structured FAQ documents
        ↓
all-MiniLM-L6-v2 normalized embeddings
        ↓
FAISS IndexFlatIP cosine search
        ↓
Top-k retrieval + similarity fallback gate
        ↓
LangChain structured prompt
        ↓
Local FLAN-T5 or OpenAI chat model
        ↓
Grounded answer + retrieved sources
```

## How RAG works

Retrieval finds relevant external information, augmentation inserts that information into the model prompt, and generation produces a natural-language answer. Separating these stages allows retrieval failures and generation failures to be measured independently.

## Dataset

The reproducible pilot contains 200 synthetic FAQs: 20 categories, 10 distinct intents per category, stable IDs, fictional approved answers, and no real personal data. It does not represent real customer traffic.

```bash
python3 scripts/generate_synthetic_dataset.py
python3 scripts/validate_raw_dataset.py
```

Use `--force` only when intentionally regenerating the protected raw CSV.

## Preprocessing

Preprocessing validates the schema, normalizes Unicode and whitespace, rejects incomplete or unusually short text, removes exact duplicates, rejects conflicting answers and duplicate IDs, preserves metadata, constructs `retrieval_text` and full `document_text`, and writes measured statistics.

```bash
python3 -m src.preprocessing
```

Measured result: 200 input rows, 200 retained rows, zero removed rows, zero exact duplicates, and 20 categories.

## Embeddings

`all-MiniLM-L6-v2` converts FAQ questions and user queries into fixed-length vectors. A controlled comparison found that question-only FAQ embeddings improved Recall@1 and mean reciprocal rank over embedding the full structured record, so the answer remains metadata for LLM context rather than retrieval text. Both vector types are L2-normalized.

## FAISS retrieval

The project uses the exact `faiss.IndexFlatIP`; inner product on normalized vectors equals cosine similarity. The returned value is a similarity—not a probability or confidence score.

The persisted index contains `index.faiss`, `documents.json`, and `manifest.json`, preserving the vector-position-to-document mapping and recording the model, dimension, count, index type, and metric.

```bash
python3 build_index.py
```

## Prompting

LangChain constructs separate system and user messages. The system instruction requires the model to use only supplied context, avoid invented policies, use a fixed insufficient-context fallback, and answer concisely.

## LLM

For dependable local demonstrations, the default no-key mode returns the approved answer from the highest-ranked FAQ after retrieval passes the similarity threshold. The local FLAN-T5 adapter remains available for generation experiments and evaluation, while the optional `ChatOpenAI` adapter uses temperature `0` and reads credentials only from the environment.

RAG reduces hallucination risk; it does not guarantee perfectly grounded answers.

## Evaluation

### Retrieval

The set contains 60 independently worded in-domain queries mapped to expected document IDs plus 10 out-of-domain queries.

```bash
python3 -m src.evaluate
```

This generates Recall@1, Recall@3, Recall@5, mean reciprocal rank at 5, out-of-domain rejection rate, and per-query details under `evaluation/results/`. Results must be inspected before being quoted.

Verified pilot results with `TOP_K=3` for the application and a `0.35` fallback threshold:

| Metric | Result |
|---|---:|
| Recall@1 | 83.3% |
| Recall@3 | 91.7% |
| Recall@5 | 96.7% |
| MRR@5 | 88.1% |
| Out-of-domain rejection | 90.0% |

These results use 60 in-domain and 10 out-of-domain queries from this synthetic pilot. They are not production benchmarks. At threshold `0.35`, all 60 in-domain queries passed the acceptance gate, while one out-of-domain income-tax query was incorrectly accepted because it was semantically close to the FAQ about sales-tax calculation.

### Response quality

```bash
python3 -m src.evaluate_responses
python3 -m src.summarize_response_evaluation
```

This generates answers for 15 representative queries. The checked-in manual review uses `0 = poor`, `1 = acceptable`, and `2 = strong` for relevance, groundedness, and fallback correctness.

Verified local baseline results:

| Metric | Mean (0–2) | Percent of maximum |
|---|---:|---:|
| Relevance | 1.00 | 50.0% |
| Groundedness | 1.13 | 56.7% |
| Fallback correctness | 1.87 | 93.3% |

The small local model performs poorly on several in-domain generations even when retrieval is correct. This is a measured limitation and demonstrates why retrieval and generation must be evaluated separately. The manual notes are in `data/evaluation/manual_response_scores.csv`; generated answers and aggregates are under `evaluation/results/`.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Rebuild the complete local pipeline with one cross-platform command:

```bash
python scripts/bootstrap_project.py
```

The bootstrap script generates and validates the synthetic dataset, preprocesses it, and builds the FAISS index. These generated artifacts are intentionally excluded from Git because they are reproducible. Run `python -m src.evaluate` separately when you want to regenerate evaluation results.

## Environment variables

```bash
cp .env.example .env
```

```text
OPENAI_API_KEY=       # required only when LLM_PROVIDER=openai
LLM_PROVIDER=local    # change to openai to use ChatOpenAI
LOCAL_LLM_MODEL=google/flan-t5-small
LLM_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=all-MiniLM-L6-v2
TOP_K=3
MIN_SIMILARITY=0.35
```

Never commit `.env`.

## Running the application

```bash
streamlit run app.py
```

The default local provider performs semantic retrieval and returns the highest-ranked approved FAQ answer without an API key. Set `LLM_PROVIDER=openai` and provide `OPENAI_API_KEY` to generate a grounded paraphrase with the optional OpenAI adapter.

The interface opens with a compact welcome card. Start a conversation or select an orders, returns, or account topic to open the messenger. Questions and answers remain visible during the current browser session, with expandable supporting FAQs beneath each answer. The settings control contains retrieval tuning and a clear-conversation action; the back arrow returns to the welcome card without clearing the conversation. Failed requests offer a retry button.

Chat history is for display only: each question is independently retrieved and answered, so write complete questions rather than relying on earlier messages for context. History is not saved across browser sessions. Visual styles live in `assets/support.css`.

The first local request can take about 30 seconds while the embedding and generation models load. Both models are cached for later questions. Streamlit file watching is disabled because its module scanner conflicts with Transformers' optional vision modules; source edits therefore require a manual server restart.

## Testing

```bash
python -m pytest -q
```

Tests cover dataset generation, preprocessing, FAISS persistence, retrieval ranking and thresholds, prompt context flow, fallback behavior, metric calculation, and messenger navigation, source display, retries, and safe message rendering. Model downloads and paid API calls are excluded from unit tests.

## Example queries

```text
I forgot my password. How can I get back into my account?
The courier says delivered, but I cannot find my parcel.
Can I transfer my reward points to someone else?
Someone claiming to be support asked for my password.
```

Out-of-domain example: `What will tomorrow's weather be?`

## Error analysis

Inspect `retrieval_details.csv` for missing expected documents, correct documents ranked below overlapping intents, weak similarities for valid questions, high similarities for out-of-domain questions, and threshold errors. Retrieval failures and generation failures must be analyzed separately.

Two expected documents were absent from the top five: a guest-checkout query was confused with sign-in support, and a subscription-cancellation query was confused with pausing a subscription. These are useful examples of overlapping intent language rather than results to hide.

## Limitations

- The knowledge base is synthetic, small, and artificially balanced.
- The evaluation set was manually authored for this project.
- A global similarity threshold is an imperfect out-of-domain detector.
- Exact FAISS search fits this pilot, not necessarily a production-scale corpus.
- Response quality depends on the configured model and requires human review.
- The app has no authentication, rate limiting, persistent chat history, monitoring, or production security controls.

## Future improvements

Improvements should follow measured errors. Candidates include expanding difficult intents, larger threshold-calibration sets, metadata filtering, reranking, clarification for ambiguous questions, groundedness checks, latency measurement, and production security controls.

## Project structure

```text
.
├── app.py
├── build_index.py
├── data/{raw,processed,evaluation}/
├── evaluation/results/
├── scripts/
├── src/
├── tests/
├── vectorstore/faiss_index/
├── .env.example
├── .python-version
├── requirements.txt
└── requirements-dev.txt
```
