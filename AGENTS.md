# Repository Guidelines

## Project Structure & Module Organization

This repository is a Phase 0 monorepo skeleton for `AI Courtroom Harness`.

- `apps/api/`: FastAPI mock API and contract endpoints.
- `apps/web/`: frontend workspace placeholder.
- `packages/shared/`: shared contracts and fixtures.
  - `python/ai_court_shared/schemas.py`: Pydantic source of truth.
  - `types/index.ts`: mirrored TypeScript types.
  - `fixtures/`: sample case, parse, and simulation payloads.
- `packages/retrieval/`, `orchestration/`, `verification/`, `reporting/`: implementation packages for later phases.
- `scripts/`: ingest, eval, and demo entrypoints.
- `docs/`: architecture, prompt, and evaluation notes.

## Build, Test, and Development Commands

Run commands from the repository root unless noted otherwise.

- `python -m venv .venv`: create the required local Python environment.
- `.venv\Scripts\Activate.ps1`: activate the virtual environment in PowerShell.
- `python -m pip install -e .`: install project dependencies into `.venv`.
- `python -m compileall apps packages`: quick Python smoke check.
- `uvicorn app.main:app --reload`: run the mock API from `apps/api`.
- `git status --short --branch`: verify workspace state before commit/push.

## Dependency and API Usage Policy

Prefer existing libraries, SDKs, and official APIs over custom hardcoded implementations.

- Do not reimplement functionality already covered by stable libraries such as parsing, validation, HTTP clients, vector search integrations, or document processing.
- Use framework features before writing manual glue code.
- If you choose a custom implementation, explain why the existing library or API support is insufficient.
- Avoid hardcoded logic when config, schema-driven code, or API responses can be the source of truth.

## Coding Style & Naming Conventions

- Use 4 spaces in Python and keep imports explicit.
- Keep Python and TypeScript contracts aligned whenever schemas change.
- Prefer ASCII unless a file already contains Vietnamese content.
- Write contributor-facing documentation in English by default, especially `README.md`, `AGENTS.md`, setup guides, and package-level docs.
- Use predictable fixture names such as `sample_case_01.*.json`.
- Use uppercase ID prefixes in payloads: `CASE_001`, `EVID_001`, `LAW_001`, `TURN_001`.

## Testing Guidelines

- Validate contract changes against the sample fixtures in `packages/shared/fixtures/`.
- Keep `apps/api/app/main.py` synced with fixture and schema shapes.
- Add future tests near the owning module with names like `test_<behavior>.py`.

## Commit, Push & Pull Request Guidelines

After each completed task: validate, commit, and push unless explicitly told not to.

- Format commits as `<type>: <short summary>`.
- Preferred types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`.
- Examples: `feat: add legal-search request schema`, `fix: align simulation fixture with shared contracts`.
- Keep each commit scoped to one logical change.

For PRs, include purpose, affected modules, contract changes, validation steps, and screenshots or sample payloads when UI/API behavior changes.

## Environment Rule

All Python work must use the repo-local `.venv`. Do not run project commands against the global interpreter, and do not install dependencies globally for this repository.
