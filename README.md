# AI Courtroom Harness

Phase 0 skeleton for `AI Courtroom Harness`.

The goal of this skeleton is to lock down:

- Repo structure
- Shared domain contracts
- Mock fixtures
- Minimal API shape

so frontend, backend, retrieval, and orchestration can be developed in parallel.

## Workspace Layout

```text
apps/
  api/         FastAPI mock API for Phase 0
  web/         frontend workspace placeholder
packages/
  shared/      shared schemas and fixtures
  retrieval/   retrieval module placeholder
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

These endpoints currently return fixtures and are intended to lock contracts for Phase 0.

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

## Run API Mock

```bash
uvicorn app.main:app --reload
```

Run from:

```text
apps/api
```
