# AI Courtroom Harness

Phase 0 foundation plus early Phase 1 and Phase 2 baselines for `AI Courtroom Harness`.

The goal of this skeleton is to lock down:

- Repo structure
- Shared domain contracts
- Mock fixtures
- Minimal API shape
- A local retrieval baseline for legal search
- A CPU-friendly case intake and parsing baseline

so frontend, backend, retrieval, and orchestration can be developed in parallel.

## Workspace Layout

```text
apps/
  api/         FastAPI mock API for Phase 0
  web/         frontend workspace placeholder
packages/
  shared/      shared schemas and fixtures
  retrieval/   retrieval baseline, seed corpus, and ingest helpers
  orchestration/ orchestration module placeholder
  verification/ verification module placeholder
  reporting/   reporting module placeholder
data/
  raw/
  processed/
  indexes/
scripts/
  ingest/
  eval/
  demos/
docs/
  architecture/
  prompts/
  eval/
```

## FastAPI Endpoints

- `GET /health`
- `GET /api/v1/fixtures/sample-case`
- `GET /api/v1/cases`
- `POST /api/v1/cases`
- `GET /api/v1/cases/{case_id}`
- `POST /api/v1/cases/{case_id}/attachments`
- `POST /api/v1/cases/{case_id}/parse`
- `GET /api/v1/cases/{case_id}/state`
- `GET /api/v1/cases/{case_id}/audit`
- `POST /api/v1/legal-search`
- `POST /api/v1/cases/{case_id}/simulate`
- `POST /api/v1/cases/{case_id}/review`
- `GET /api/v1/reports/{case_id}`
- `POST /api/v1/reports/{case_id}/markdown`
- `GET /api/v1/reports/{case_id}/markdown`

- `POST /api/v1/cases` now persists draft case input to a local SQLite store and writes case snapshots to `data/processed/cases/<case_id>/case.json`
- `GET /api/v1/cases` lists locally created cases from the persistence layer
- `GET /api/v1/cases/{case_id}` returns draft input plus the latest parsed state when available
- `POST /api/v1/cases/{case_id}/attachments` uploads a local attachment into `data/raw/cases/<case_id>/attachments/` and resets the case back to `draft` until it is parsed again
- `POST /api/v1/cases/{case_id}/parse` now runs a local heuristic parser and persists `parsed.json`
- `GET /api/v1/cases/{case_id}/state` returns the stored parsed case state for frontend consumption
- `GET /api/v1/cases/{case_id}/audit` returns the persisted audit trail and human review gate
- `POST /api/v1/cases/{case_id}/simulate` now runs a LangGraph-based courtroom simulation flow over the parsed case state
- `POST /api/v1/cases/{case_id}/review` resolves the human review gate and can move a case from `review_required` to `report_ready`
- `GET /api/v1/reports/{case_id}` now returns the latest stored simulation report when available, and falls back to the fixture only for the sample case without a local simulation snapshot
- `POST /api/v1/reports/{case_id}/markdown` exports a persisted markdown report once the case is `report_ready`
- `GET /api/v1/reports/{case_id}/markdown` reads the stored markdown export for the case
- `POST /api/v1/legal-search` uses the retrieval baseline over the MVP legal corpus
- Attachment parsing is CPU-friendly and supports metadata parsing for all attachments plus best-effort local text extraction for PDF and text files when `local_path` is provided

## Shared Contracts

Python schemas:

- `packages/shared/python/ai_court_shared/schemas.py`

TypeScript types:

- `packages/shared/types/index.ts`

## Sample Fixtures

- `packages/shared/fixtures/sample_case_01.case.json`
- `packages/shared/fixtures/sample_case_01.create.response.json`
- `packages/shared/fixtures/sample_case_01.parse.json`
- `packages/shared/fixtures/sample_case_01.report.json`
- `packages/shared/fixtures/sample_case_01.simulation.json`

## Retrieval Baseline

- Real MVP corpus: `packages/retrieval/python/ai_court_retrieval/resources/mvp_legal_corpus.json`
- Fallback seed corpus: `packages/retrieval/python/ai_court_retrieval/resources/seed_legal_corpus.json`
- Search service: `packages/retrieval/python/ai_court_retrieval/service.py`
- Ingest helper: `scripts/ingest/build_legal_corpus.py`
- Smoke eval: `scripts/eval/smoke_legal_search.py`
- Optional full-corpus dependency: install `datasets` inside `.venv` before running the ingest helper
- Remote vector setup guide: `docs/COLAB_VECTOR_SETUP.md`

Run a retrieval smoke check from the repo root:

```bash
.\.venv\Scripts\python scripts/eval/smoke_legal_search.py
```

To enable hybrid search without running the embedding model on your laptop, set:

```powershell
$env:AI_COURT_VECTOR_API_URL="https://your-colab-ngrok-url"
```

The local API will then merge BM25 with remote vector results from Colab and fall back to BM25-only if the remote service is unavailable.

## Run API Mock

```bash
uvicorn app.main:app --reload
```

Run from:

```text
apps/api
```

## Phase 2 Smoke Check

The Phase 2 baseline is CPU-only and does not require a GPU. Run:

```bash
.\.venv\Scripts\python scripts/eval/smoke_case_intake.py
```

This creates a draft case, uploads a PDF attachment, parses it into facts, evidence, and legal issues, and writes the artifacts to `data/processed/cases/`.

## Phase 3 Smoke Check

The Phase 3 simulation runtime is also CPU-only. Run:

```bash
.\.venv\Scripts\python scripts/eval/smoke_simulation.py
```

This drives `create -> upload attachment -> parse -> simulate -> report` through the FastAPI app and verifies that the LangGraph-based multi-agent flow produces structured claims, turns, minutes, and a final report.

## LLM Providers

The courtroom runtime now supports a provider abstraction for text generation in the
`plaintiff`, `defense`, `judge`, and `clerk` stages while preserving heuristic fallback.

OpenRouter setup:

```powershell
$env:AI_COURT_LLM_PROVIDER="openrouter"
$env:OPENROUTER_API_KEY="your_key_here"
$env:OPENROUTER_MODEL="inclusionai/ring-2.6-1t:free"
```

Groq setup:

```powershell
$env:AI_COURT_LLM_PROVIDER="groq"
$env:GROQ_API_KEY="your_key_here"
$env:GROQ_MODEL="qwen/qwen3-32b"
```

If `AI_COURT_LLM_PROVIDER` is left as `auto`, the runtime currently prefers OpenRouter when
`OPENROUTER_API_KEY` is present, otherwise Groq when `GROQ_API_KEY` is present, and otherwise
falls back to the deterministic heuristic path.

Optional model override:

```powershell
$env:OPENROUTER_MODEL="tencent/hy3-preview"
```

The runtime does not persist API keys. Keep them in the current shell only.

Quick provider smoke:

```bash
.\.venv\Scripts\python scripts/eval/smoke_openrouter_provider.py
```

Benchmark notes and recommended models:

- `docs/MODEL_BENCHMARKS.md`

## Phase 4 Safety Check

The same simulation smoke now also verifies:

- audit trail creation
- unsupported claim and citation checks
- human review gate activation
- report status transitioning to `review_required` when risks remain

## Phase 5 Backend Check

The Phase 5 backend additions are still CPU-only. Run:

```bash
.\.venv\Scripts\python scripts/eval/smoke_review_export.py
```

This drives `create -> upload attachment -> parse -> simulate -> review approve -> markdown export`
and verifies that the review gate can be resolved into `report_ready` before exporting
`data/processed/cases/<case_id>/report.md`.
