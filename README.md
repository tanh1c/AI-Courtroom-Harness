# AI Courtroom Harness

Phase 0 skeleton cho `AI Courtroom Harness`.

Mục tiêu của skeleton này là khóa:

- Repo structure
- Shared domain contracts
- Mock fixtures
- API shape tối thiểu

để frontend, backend, retrieval và orchestration có thể triển khai song song.

## Workspace Layout

```text
apps/
  api/         FastAPI mock API cho Phase 0
  web/         placeholder cho frontend workspace
packages/
  shared/      schemas + fixtures dùng chung
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
- `POST /api/v1/cases/parse`
- `POST /api/v1/legal-search`
- `POST /api/v1/cases/simulate`

Các endpoint hiện tại trả về fixtures và được thiết kế để khóa contract cho Phase 0.

## Shared Contracts

Python schemas:

- `packages/shared/python/ai_court_shared/schemas.py`

TypeScript types:

- `packages/shared/types/index.ts`

## Sample Fixtures

- `packages/shared/fixtures/sample_case_01.case.json`
- `packages/shared/fixtures/sample_case_01.parse.json`
- `packages/shared/fixtures/sample_case_01.simulation.json`

## Run API Mock

```bash
uvicorn app.main:app --reload
```

Run from:

```text
apps/api
```

