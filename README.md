# AI Courtroom Harness

Phase 0 foundation plus an early Phase 1 retrieval baseline for `AI Courtroom Harness`.

The goal of this skeleton is to lock down:

- Repo structure
- Shared domain contracts
- Mock fixtures
- Minimal API shape
- A local retrieval baseline for legal search

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

## FastAPI Mock Endpoints

- `GET /health`
- `GET /api/v1/fixtures/sample-case`
- `POST /api/v1/cases`
- `POST /api/v1/cases/{case_id}/parse`
- `POST /api/v1/legal-search`
- `POST /api/v1/cases/{case_id}/simulate`
- `GET /api/v1/reports/{case_id}`

The case and report endpoints still return fixtures. The legal search endpoint now uses a local BM25 retrieval baseline backed by a seed legal corpus.

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
