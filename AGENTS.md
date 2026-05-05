# Repository Guidelines

## Project Structure & Module Organization

This repository is a Phase 0 monorepo skeleton for `AI Courtroom Harness`.

- `apps/api/`: FastAPI mock API used to lock backend contracts.
- `apps/web/`: frontend workspace placeholder.
- `packages/shared/`: shared contracts and fixtures.
  - `python/ai_court_shared/schemas.py`: Pydantic source of truth.
  - `types/index.ts`: mirrored TypeScript types.
  - `fixtures/`: sample case, parse, and simulation payloads.
- `packages/retrieval/`, `orchestration/`, `verification/`, `reporting/`: feature packages to be implemented by later phases.
- `scripts/`: ingest, eval, and demo entrypoints.
- `docs/`: architecture, prompts, and evaluation notes.

## Build, Test, and Development Commands

Run commands from the repository root unless noted otherwise.

- `python -m compileall apps packages`: quick Python smoke check.
- `@' ... '@ | python -`: use short inline scripts to validate fixtures against Pydantic models when changing contracts.
- `uvicorn app.main:app --reload`: run the mock API from `apps/api`.
- `git status --short --branch`: confirm the working tree before committing.

There is no frontend build pipeline yet; `package.json` and `pnpm-workspace.yaml` only reserve workspace structure for later phases.

## Coding Style & Naming Conventions

- Use 4 spaces in Python and keep imports simple and explicit.
- Keep schemas aligned across Python and TypeScript whenever contracts change.
- Prefer ASCII unless a file already contains Vietnamese copy.
- Name fixtures and sample data predictably, for example `sample_case_01.*.json`.
- Use uppercase ID prefixes in payloads: `CASE_001`, `EVID_001`, `LAW_001`, `TURN_001`.

## Testing Guidelines

Formal test suites are not added yet. Until then:

- Validate every contract change against the sample fixtures.
- Keep mock endpoints in `apps/api/app/main.py` in sync with fixture shapes.
- Add future tests near the owning module, and use names like `test_<behavior>.py`.

## Commit, Push & Pull Request Guidelines

After finishing a discrete task, contributors should:

- run the relevant validation or smoke checks,
- commit the completed work,
- push the branch to the remote repository.

Use Conventional Commit style so history is easy to scan and track:

- `feat: add legal-search request schema`
- `fix: align simulation fixture with shared contracts`
- `chore: scaffold verification package`
- `docs: update implementation plan`

Rules:

- Format commits as `<type>: <short summary>`.
- Prefer `feat`, `fix`, `chore`, `docs`, `refactor`, `test`.
- Keep each commit scoped to one task or one logical change.
- Push after each completed task unless the user explicitly asks to hold changes locally.

For PRs, include: purpose, affected modules, contract changes, validation steps, and screenshots or sample payloads when UI/API behavior changes.

## Architecture Notes

This project is harness-first, not chatbot-first. Treat `packages/shared` as the contract boundary that lets frontend, retrieval, orchestration, and verification work in parallel.
