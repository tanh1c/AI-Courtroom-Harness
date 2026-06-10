# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## Project overview

AI Courtroom Harness is a Vietnamese legal workflow simulator and review system. The repo is organized as a small Python/TypeScript monorepo with a FastAPI backend, a Vite/React frontend, and shared Pydantic/TypeScript contracts that keep the API, fixtures, and UI in sync.

The product has three main runtime layers:

- **Case intake / parsing**: creates cases, stores attachments, parses text/PDF evidence, and materializes structured case state.
- **Courtroom runtime**: runs the MVP/V1/V2 simulation flows, retrieval, verification, human review, and report export.
- **Inspection UI**: renders cases, timelines, transcript/state, review actions, and report previews against the backend API.

The shared schema layer is the source of truth. When contracts change, update backend code, fixtures, and frontend types together.

## Big-picture architecture

- `apps/api/` is the HTTP boundary. It wires FastAPI routes to case storage, parsing, retrieval, simulation, reporting, verification, and review flows.
- `packages/shared/` holds the canonical Pydantic schemas plus fixtures used by the backend and frontend.
- `packages/retrieval/` owns legal retrieval and citation generation. It is BM25-first with optional vector retrieval support.
- `packages/orchestration/` owns the courtroom runtimes. V2 is the stage-based simulation flow and can optionally polish selected dialogue turns with an LLM provider; deterministic fallback remains the default.
- `packages/verification/` applies fact/citation checks, audit trail generation, and human-review gating.
- `packages/reporting/` renders markdown and HTML reports for hearing and trial records.
- `frontend/` is a Vite React workspace for the courtroom inspection UI.
- `scripts/` contains ingest, eval, demo, and setup entrypoints. Demo scripts are part of the repo workflow, not just examples.
- `docs/` contains architecture notes, eval notes, prompt notes, and migration notes.

## Important repo conventions

- Use the repo-local `.venv` for all Python work.
- Keep Python and frontend contract shapes aligned.
- Prefer absolute, explicit imports.
- Prefer schema-driven code over hardcoded glue when a contract or fixture can be the source of truth.
- Treat all legal outputs as non-binding simulation artifacts.

## Common commands

Run commands from the repository root unless noted otherwise.

### Python environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

### Backend

```powershell
npm run dev:api
```

Equivalent direct command:

```powershell
.\.venv\Scripts\python.exe -m uvicorn apps.api.app.main:app --reload
```

### Frontend

```powershell
npm run dev:web
```

### Typecheck / lint

```powershell
npm run typecheck
```

Frontend package lint command:

```powershell
npm --prefix frontend run lint
```

### Python smoke checks

```powershell
.\.venv\Scripts\python.exe -m compileall apps packages scripts\eval
```

### Evaluation and smoke tests

```powershell
.\.venv\Scripts\python.exe scripts\eval\smoke_case_intake.py
.\.venv\Scripts\python.exe scripts\eval\smoke_legal_search.py
.\.venv\Scripts\python.exe scripts\eval\smoke_simulation.py
.\.venv\Scripts\python.exe scripts\eval\smoke_review_export.py
.\.venv\Scripts\python.exe scripts\eval\smoke_v1_hearing_runtime.py
.\.venv\Scripts\python.exe scripts\eval\smoke_v1_eval_cases.py
.\.venv\Scripts\python.exe scripts\eval\smoke_v1_negative_guards.py
.\.venv\Scripts\python.exe scripts\eval\smoke_v2_trial_runtime.py
.\.venv\Scripts\python.exe scripts\eval\smoke_v2_eval_cases.py
```

### Single test or single smoke script

Use pytest for unit/eval tests when they exist:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\eval\test_name.py -v
.\.venv\Scripts\python.exe -m pytest tests\eval\test_name.py::test_case_name -v
```

Run one script directly when it is a standalone smoke/eval entrypoint:

```powershell
.\.venv\Scripts\python.exe scripts\eval\smoke_v2_trial_runtime.py
```

### Demos

```powershell
.\scripts\demos\run_demo.ps1
.\scripts\demos\run_demo.ps1 -OpenPreview
.\.venv\Scripts\python.exe scripts\demos\run_v2_full_trial_demo.py
.\.venv\Scripts\python.exe scripts\demos\generate_v2_evidence_bundle.py
```

## Where to look first

If you need to understand the product flow, start with these files:

- `README.md` for the current product story, setup, APIs, and smoke commands.
- `apps/api/app/main.py` for the actual API surface and orchestration of parsing/simulation/review/reporting.
- `packages/shared/python/ai_court_shared/schemas.py` for the canonical data contracts.
- `packages/orchestration/python/ai_court_orchestration/v2_service.py` for the main courtroom runtime and guard logic.
- `packages/retrieval/python/ai_court_retrieval/service.py` for retrieval strategy and citation selection.
- `packages/verification/python/ai_court_verification/service.py` for fact/citation checks and human-review gating.
- `frontend/src/App.tsx` and `frontend/src/api.ts` for the UI state model and API contract.

## Runtime and product notes

- The orchestration package is schema-first and retrieval-grounded.
- V2 can use provider-backed dialogue polishing when enabled, but it must fall back to deterministic text if the provider is unavailable or produces unsupported output.
- The default MVP provider chain is OpenRouter `inclusionai/ring-2.6-1t:free`, then Groq `qwen/qwen3-32b`, then heuristic runtime text.
- The repository has demo scripts that create and export legal workflow artifacts end-to-end; they are part of the main product story.

## When modifying contracts

If you change any shared schema or API payload:

1. Update the Pydantic schema in `packages/shared/python/ai_court_shared/schemas.py`.
2. Update backend producers/consumers.
3. Update frontend types and request/response handling in `frontend/src/api.ts`.
4. Update fixtures in `packages/shared/fixtures/`.
5. Re-run compile/typecheck and the relevant smoke scripts.

## Validation checklist

Before reporting backend or workflow changes as done, run the relevant checks from the repo-local `.venv`, plus frontend lint if the UI changed.

- Python compile: `python -m compileall apps packages scripts\eval`
- Frontend typecheck: `npm run typecheck`
- Frontend lint: `npm --prefix frontend run lint`
- Relevant smoke/eval script(s) for the affected flow

## Notes from repository guidance

- Contributor-facing docs should be written in English unless the file already uses Vietnamese content.
- Fixture IDs use uppercase prefixes such as `CASE_001`, `EVID_001`, `LAW_001`, `TURN_001`.
- Use predictable fixture names like `sample_case_01.*.json`.
- Keep current work scoped to the repo-local virtual environment and the existing monorepo layout.
