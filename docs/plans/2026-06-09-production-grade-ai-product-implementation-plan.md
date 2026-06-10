# Production-Grade AI Product Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn AI Courtroom Harness into a production-grade AI legal workflow product with reproducible ingestion, hybrid retrieval, graph-based orchestration, eval-driven guardrails, observability, human review, and an inspection-first frontend.

**Architecture:** Keep FastAPI as the backend entry point and React/Vite as the inspection UI. Introduce a canonical document pipeline, hybrid retrieval layer, graph-based workflow runtime, evaluation harness, and observability stack without overcomplicating the current legal domain scope.

**Tech Stack:** FastAPI, React/Vite, TypeScript, Python 3.12+, Docling, OCRmyPDF, Qdrant, LangGraph, DeepEval, RAGAS, Promptfoo, Langfuse, Presidio, LLM Guard, Docker Compose, PostgreSQL.

---

## Phase 1: Foundation and Reproducibility

### Task 1: Fix package installation and imports

**Files:**
- Modify: `pyproject.toml`
- Modify: `apps/api/app/main.py`
- Modify: `packages/retrieval/python/ai_court_retrieval/service.py`
- Modify: `packages/orchestration/python/ai_court_orchestration/service.py`
- Modify: `packages/orchestration/python/ai_court_orchestration/v1_service.py`
- Modify: `packages/orchestration/python/ai_court_orchestration/v2_service.py`
- Modify: `packages/reporting/python/ai_court_reporting/service.py`
- Modify: `packages/verification/python/ai_court_verification/service.py`

**Step 1: Write the failing test**
- Add a smoke test that imports `apps.api.app.main` and the package entrypoints from a clean interpreter.
- Keep it minimal and assert import success without manual `sys.path` hacks.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/smoke/test_imports.py -v`
- Expected: import failure or packaging failure before the fix.

**Step 3: Write minimal implementation**
- Expand package discovery so all backend packages install cleanly.
- Reduce `sys.path` dependence in the API bootstrap.
- Keep imports consistent and absolute.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/smoke/test_imports.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add pyproject.toml apps/api/app/main.py packages/retrieval/python/ai_court_retrieval/service.py packages/orchestration/python/ai_court_orchestration/service.py packages/orchestration/python/ai_court_orchestration/v1_service.py packages/orchestration/python/ai_court_orchestration/v2_service.py packages/reporting/python/ai_court_reporting/service.py packages/verification/python/ai_court_verification/service.py tests/smoke/test_imports.py`

### Task 2: Standardize local setup and environment docs

**Files:**
- Modify: `README.md`
- Create: `.env.example`
- Modify: `package.json`
- Modify: `frontend/package.json`

**Step 1: Write the failing test**
- Add a doc check or script check that verifies required env variables and setup commands are documented.
- If no doc test exists, write a small smoke script that validates the documented commands are present in the README.

**Step 2: Run test to verify it fails**
- Run the new doc/setup check.
- Expected: missing or inconsistent setup guidance.

**Step 3: Write minimal implementation**
- Document one canonical local setup path.
- Add `.env.example` with required keys only.
- Add root scripts that clearly invoke backend/frontend commands.

**Step 4: Run test to verify it passes**
- Run the doc/setup check again.
- Expected: PASS.

**Step 5: Commit**
- `git add README.md .env.example package.json frontend/package.json tests/...`

### Task 3: Split the frontend into maintainable inspection components

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/WorkspaceShell.tsx`
- Create: `frontend/src/components/CaseSidebar.tsx`
- Create: `frontend/src/components/ModeSwitcher.tsx`
- Create: `frontend/src/components/TracePanel.tsx`
- Create: `frontend/src/components/DocumentPanel.tsx`
- Create: `frontend/src/hooks/useCaseWorkspace.ts`

**Step 1: Write the failing test**
- Add a TypeScript compile guard or component render test if the repo already has one.
- Otherwise, add a small lint-targeted assertion by extracting props and types.

**Step 2: Run test to verify it fails**
- Run: `npm --prefix frontend run lint`
- Expected: missing component/module errors before extraction.

**Step 3: Write minimal implementation**
- Move pure UI blocks out of `App.tsx` into reusable components.
- Keep behavior unchanged.

**Step 4: Run test to verify it passes**
- Run: `npm --prefix frontend run lint`
- Expected: PASS.

**Step 5: Commit**
- `git add frontend/src/App.tsx frontend/src/components/... frontend/src/hooks/...`

---

## Phase 2: Document Ingestion and Provenance

### Task 4: Introduce a canonical document artifact model

**Files:**
- Modify: `packages/shared/python/ai_court_shared/schemas.py`
- Modify: `apps/api/app/case_parser.py`
- Modify: `apps/api/app/case_store.py`
- Modify: `packages/shared/fixtures/sample_case_01.parse.json`

**Step 1: Write the failing test**
- Add a parse-state test that asserts page/block/span provenance fields exist on parsed document artifacts.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_parse_provenance.py -v`
- Expected: missing fields or schema mismatch.

**Step 3: Write minimal implementation**
- Add a canonical document structure with source metadata and provenance.
- Persist document artifacts separately from case summaries.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_parse_provenance.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/shared/python/ai_court_shared/schemas.py apps/api/app/case_parser.py apps/api/app/case_store.py packages/shared/fixtures/sample_case_01.parse.json tests/eval/test_parse_provenance.py`

### Task 5: Add Docling-backed PDF parsing

**Files:**
- Create: `apps/api/app/document_parsing.py`
- Modify: `apps/api/app/case_parser.py`
- Modify: `pyproject.toml`
- Modify: `tests/eval/test_document_parsing.py`

**Step 1: Write the failing test**
- Add a parser test for clean PDF input and assert structured page/block output.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_document_parsing.py -v`
- Expected: parser not available or no structured output.

**Step 3: Write minimal implementation**
- Add Docling as the primary parser path.
- Keep fallback text extraction for simple cases.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_document_parsing.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add apps/api/app/document_parsing.py apps/api/app/case_parser.py pyproject.toml tests/eval/test_document_parsing.py`

### Task 6: Add OCRmyPDF as a background OCR pipeline

**Files:**
- Create: `apps/api/app/ocr_pipeline.py`
- Modify: `apps/api/app/document_parsing.py`
- Modify: `apps/api/app/case_store.py`
- Create: `tests/eval/test_ocr_pipeline.py`

**Step 1: Write the failing test**
- Add a test for a scanned PDF artifact path that expects OCR output metadata.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_ocr_pipeline.py -v`
- Expected: no OCR job/path yet.

**Step 3: Write minimal implementation**
- Implement OCR as an idempotent artifact-producing job.
- Store OCR text, warnings, and artifact references.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_ocr_pipeline.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add apps/api/app/ocr_pipeline.py apps/api/app/document_parsing.py apps/api/app/case_store.py tests/eval/test_ocr_pipeline.py`

### Task 7: Make provenance visible in the frontend

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/SourceProvenancePanel.tsx`

**Step 1: Write the failing test**
- Add a type-level assertion or render test for source provenance props.

**Step 2: Run test to verify it fails**
- Run: `npm --prefix frontend run lint`
- Expected: type errors before data shape update.

**Step 3: Write minimal implementation**
- Expose page/block/chunk provenance from API state.
- Render provenance panel in the workspace.

**Step 4: Run test to verify it passes**
- Run: `npm --prefix frontend run lint`
- Expected: PASS.

**Step 5: Commit**
- `git add frontend/src/api.ts frontend/src/App.tsx frontend/src/components/SourceProvenancePanel.tsx`

---

## Phase 3: Retrieval, RAG, and Citation Grounding

### Task 8: Add Qdrant-backed dense retrieval

**Files:**
- Create: `packages/retrieval/python/ai_court_retrieval/qdrant_client.py`
- Modify: `packages/retrieval/python/ai_court_retrieval/service.py`
- Modify: `pyproject.toml`
- Create: `tests/eval/test_hybrid_retrieval.py`

**Step 1: Write the failing test**
- Add a retrieval test that expects lexical + dense hybrid ranking behavior.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_hybrid_retrieval.py -v`
- Expected: dense retrieval path missing.

**Step 3: Write minimal implementation**
- Add Qdrant client wiring and hybrid scoring.
- Keep BM25 as fallback.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_hybrid_retrieval.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/retrieval/python/ai_court_retrieval/qdrant_client.py packages/retrieval/python/ai_court_retrieval/service.py pyproject.toml tests/eval/test_hybrid_retrieval.py`

### Task 9: Add citation provenance and effective-status metadata

**Files:**
- Modify: `packages/shared/python/ai_court_shared/schemas.py`
- Modify: `packages/retrieval/python/ai_court_retrieval/service.py`
- Modify: `packages/orchestration/python/ai_court_orchestration/v2_service.py`
- Modify: `frontend/src/api.ts`
- Create: `tests/eval/test_citation_grounding.py`

**Step 1: Write the failing test**
- Add a test that verifies citations carry source document, effective status, and retrieval metadata.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_citation_grounding.py -v`
- Expected: old citation model lacks required fields.

**Step 3: Write minimal implementation**
- Extend citation schema.
- Ensure retrieval and runtime populate metadata.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_citation_grounding.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/shared/python/ai_court_shared/schemas.py packages/retrieval/python/ai_court_retrieval/service.py packages/orchestration/python/ai_court_orchestration/v2_service.py frontend/src/api.ts tests/eval/test_citation_grounding.py`

### Task 10: Build a retrieval benchmark dataset and metrics

**Files:**
- Create: `tests/eval/retrieval_cases.jsonl`
- Create: `scripts/eval/evaluate_retrieval.py`
- Create: `tests/eval/test_retrieval_eval_cli.py`

**Step 1: Write the failing test**
- Add a CLI test that expects retrieval metrics output for a small fixture set.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_retrieval_eval_cli.py -v`
- Expected: CLI or metric output missing.

**Step 3: Write minimal implementation**
- Implement offline metric computation for recall@k, MRR, nDCG.
- Emit JSON and markdown summaries.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_retrieval_eval_cli.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add tests/eval/retrieval_cases.jsonl scripts/eval/evaluate_retrieval.py tests/eval/test_retrieval_eval_cli.py`

---

## Phase 4: Graph-Based Agent Runtime

### Task 11: Introduce LangGraph workflow scaffolding

**Files:**
- Create: `packages/orchestration/python/ai_court_orchestration/graph.py`
- Modify: `packages/orchestration/python/ai_court_orchestration/v2_service.py`
- Create: `tests/eval/test_graph_workflow.py`

**Step 1: Write the failing test**
- Add a workflow test that asserts the expected graph nodes run in order.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_graph_workflow.py -v`
- Expected: graph module or node wiring missing.

**Step 3: Write minimal implementation**
- Create a graph wrapper around the current V2 runtime.
- Preserve current behavior, but route through nodes.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_graph_workflow.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/orchestration/python/ai_court_orchestration/graph.py packages/orchestration/python/ai_court_orchestration/v2_service.py tests/eval/test_graph_workflow.py`

### Task 12: Split generation, verification, and policy enforcement

**Files:**
- Modify: `packages/orchestration/python/ai_court_orchestration/v2_service.py`
- Create: `packages/orchestration/python/ai_court_orchestration/policy.py`
- Create: `packages/orchestration/python/ai_court_orchestration/verifier.py`
- Create: `tests/eval/test_policy_guards.py`

**Step 1: Write the failing test**
- Add tests for unsupported claims, official-language blocking, and review routing.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_policy_guards.py -v`
- Expected: missing policy module or guard logic.

**Step 3: Write minimal implementation**
- Move policy checks into a deterministic guard layer.
- Keep LLM generation separate from policy decisions.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_policy_guards.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/orchestration/python/ai_court_orchestration/v2_service.py packages/orchestration/python/ai_court_orchestration/policy.py packages/orchestration/python/ai_court_orchestration/verifier.py tests/eval/test_policy_guards.py`

### Task 13: Add deterministic replay for workflow runs

**Files:**
- Create: `packages/orchestration/python/ai_court_orchestration/replay.py`
- Modify: `apps/api/app/main.py`
- Create: `tests/eval/test_replay_mode.py`

**Step 1: Write the failing test**
- Add a test that replays a saved run and expects identical key outputs.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_replay_mode.py -v`
- Expected: replay mode missing.

**Step 3: Write minimal implementation**
- Persist inputs/outputs for a run and reconstruct the same trace.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_replay_mode.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/orchestration/python/ai_court_orchestration/replay.py apps/api/app/main.py tests/eval/test_replay_mode.py`

---

## Phase 5: Evaluation Harness and Quality Gates

### Task 14: Add versioned eval case fixtures

**Files:**
- Create: `tests/eval/fixtures/`
- Create: `tests/eval/fixtures/case_retrieval.json`
- Create: `tests/eval/fixtures/case_grounding.json`
- Create: `tests/eval/fixtures/case_safety.json`

**Step 1: Write the failing test**
- Add a loader test that expects versioned eval fixtures to exist and parse.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_eval_fixtures.py -v`
- Expected: fixtures missing.

**Step 3: Write minimal implementation**
- Add small gold cases and expected outcomes.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_eval_fixtures.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add tests/eval/fixtures tests/eval/test_eval_fixtures.py`

### Task 15: Build DeepEval/RAGAS/Promptfoo regression runners

**Files:**
- Create: `scripts/eval/run_ai_evals.py`
- Create: `scripts/eval/run_promptfoo.sh` or `.ps1`
- Create: `tests/eval/test_eval_runner.py`

**Step 1: Write the failing test**
- Add a test that expects a structured evaluation summary object.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_eval_runner.py -v`
- Expected: runner missing.

**Step 3: Write minimal implementation**
- Orchestrate retrieval, grounding, and safety checks into one runner.
- Emit JSON and markdown summary files.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_eval_runner.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add scripts/eval/run_ai_evals.py scripts/eval/run_promptfoo.sh tests/eval/test_eval_runner.py`

### Task 16: Wire eval thresholds into CI

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `tests/eval/test_ci_thresholds.py`

**Step 1: Write the failing test**
- Add a small test that checks threshold config structure exists.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_ci_thresholds.py -v`
- Expected: no threshold config yet.

**Step 3: Write minimal implementation**
- Add CI steps for lint, typecheck, backend tests, and lightweight eval smoke.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_ci_thresholds.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add .github/workflows/ci.yml tests/eval/test_ci_thresholds.py`

---

## Phase 6: Observability, Audit, and Human Review

### Task 17: Add trace IDs and run metadata

**Files:**
- Modify: `apps/api/app/main.py`
- Modify: `packages/orchestration/python/ai_court_orchestration/v2_service.py`
- Create: `packages/shared/python/ai_court_shared/tracing.py`
- Create: `tests/eval/test_run_metadata.py`

**Step 1: Write the failing test**
- Add a run metadata test that expects run IDs and per-step metadata.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_run_metadata.py -v`
- Expected: metadata missing.

**Step 3: Write minimal implementation**
- Generate a run ID and attach it to workflow artifacts.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_run_metadata.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add apps/api/app/main.py packages/orchestration/python/ai_court_orchestration/v2_service.py packages/shared/python/ai_court_shared/tracing.py tests/eval/test_run_metadata.py`

### Task 18: Integrate Langfuse or Phoenix traces

**Files:**
- Create: `packages/shared/python/ai_court_shared/observability.py`
- Modify: `apps/api/app/main.py`
- Modify: `packages/orchestration/python/ai_court_orchestration/service.py`
- Create: `tests/eval/test_observability_hooks.py`

**Step 1: Write the failing test**
- Add a test that expects observability hooks to receive structured events.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_observability_hooks.py -v`
- Expected: no hooks.

**Step 3: Write minimal implementation**
- Add event emitters for retrieval, LLM, policy, and review steps.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_observability_hooks.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/shared/python/ai_court_shared/observability.py apps/api/app/main.py packages/orchestration/python/ai_court_orchestration/service.py tests/eval/test_observability_hooks.py`

### Task 19: Add human review audit model and UI actions

**Files:**
- Modify: `packages/shared/python/ai_court_shared/schemas.py`
- Modify: `apps/api/app/main.py`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`
- Create: `tests/eval/test_human_review_audit.py`

**Step 1: Write the failing test**
- Add an API test that expects reviewer identity, decision, timestamp, and checklist updates to persist.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_human_review_audit.py -v`
- Expected: review record not rich enough.

**Step 3: Write minimal implementation**
- Store review records as first-class artifacts.
- Add approve/reject/request-more-evidence actions in the UI.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_human_review_audit.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/shared/python/ai_court_shared/schemas.py apps/api/app/main.py frontend/src/api.ts frontend/src/App.tsx tests/eval/test_human_review_audit.py`

---

## Phase 7: Product UI as AI Inspection Console

### Task 20: Build source-to-claim-to-report inspection panels

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/ClaimGroundingPanel.tsx`
- Create: `frontend/src/components/CitationProvenancePanel.tsx`
- Create: `frontend/src/components/ReportAuditPanel.tsx`

**Step 1: Write the failing test**
- Add a render or type test that expects the new inspection panels.

**Step 2: Run test to verify it fails**
- Run: `npm --prefix frontend run lint`
- Expected: missing component props or imports.

**Step 3: Write minimal implementation**
- Render claim grounding, citation provenance, and report audit data.

**Step 4: Run test to verify it passes**
- Run: `npm --prefix frontend run lint`
- Expected: PASS.

**Step 5: Commit**
- `git add frontend/src/App.tsx frontend/src/components/ClaimGroundingPanel.tsx frontend/src/components/CitationProvenancePanel.tsx frontend/src/components/ReportAuditPanel.tsx`

### Task 21: Add trace and eval dashboards in the UI

**Files:**
- Modify: `frontend/src/api.ts`
- Create: `frontend/src/components/TraceDashboard.tsx`
- Create: `frontend/src/components/EvalDashboard.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Write the failing test**
- Add a type/test assertion for trace and eval dashboard props.

**Step 2: Run test to verify it fails**
- Run: `npm --prefix frontend run lint`
- Expected: missing fields or props.

**Step 3: Write minimal implementation**
- Expose trace summaries, latencies, scores, and eval status.

**Step 4: Run test to verify it passes**
- Run: `npm --prefix frontend run lint`
- Expected: PASS.

**Step 5: Commit**
- `git add frontend/src/api.ts frontend/src/components/TraceDashboard.tsx frontend/src/components/EvalDashboard.tsx frontend/src/App.tsx`

---

## Phase 8: Security, Deployment, and Hardening

### Task 22: Add upload hardening and prompt injection tests

**Files:**
- Create: `packages/shared/python/ai_court_shared/security.py`
- Modify: `apps/api/app/main.py`
- Create: `tests/eval/test_prompt_injection_defense.py`
- Create: `tests/eval/test_upload_security.py`

**Step 1: Write the failing test**
- Add a malicious-document fixture test that expects the system to treat content as data.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_prompt_injection_defense.py -v`
- Expected: no prompt injection defense.

**Step 3: Write minimal implementation**
- Add file type/size checks, content handling rules, and scanner hooks.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_prompt_injection_defense.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/shared/python/ai_court_shared/security.py apps/api/app/main.py tests/eval/test_prompt_injection_defense.py tests/eval/test_upload_security.py`

### Task 23: Add PII redaction to logs and traces

**Files:**
- Create: `packages/shared/python/ai_court_shared/redaction.py`
- Modify: `packages/shared/python/ai_court_shared/observability.py`
- Create: `tests/eval/test_pii_redaction.py`

**Step 1: Write the failing test**
- Add a test that expects names, addresses, and IDs to be redacted from exported logs.

**Step 2: Run test to verify it fails**
- Run: `python -m pytest tests/eval/test_pii_redaction.py -v`
- Expected: raw text still visible.

**Step 3: Write minimal implementation**
- Redact sensitive content before logs/traces are persisted.

**Step 4: Run test to verify it passes**
- Run: `python -m pytest tests/eval/test_pii_redaction.py -v`
- Expected: PASS.

**Step 5: Commit**
- `git add packages/shared/python/ai_court_shared/redaction.py packages/shared/python/ai_court_shared/observability.py tests/eval/test_pii_redaction.py`

### Task 24: Add Docker Compose and final CI hardening

**Files:**
- Create: `docker-compose.yml`
- Create: `Dockerfile.api`
- Create: `Dockerfile.frontend`
- Modify: `.github/workflows/ci.yml`
- Modify: `README.md`

**Step 1: Write the failing test**
- Add a smoke script or docs check for Docker Compose and CI commands.

**Step 2: Run test to verify it fails**
- Run the compose or doc check.
- Expected: missing container configuration.

**Step 3: Write minimal implementation**
- Build local services for API, frontend, PostgreSQL, Qdrant, and optional observability.
- Ensure CI runs lint/typecheck/tests/eval smoke.

**Step 4: Run test to verify it passes**
- Run: `docker compose config` and the CI smoke checks.
- Expected: valid compose config and passing smoke suite.

**Step 5: Commit**
- `git add docker-compose.yml Dockerfile.api Dockerfile.frontend .github/workflows/ci.yml README.md`

---

## Phase 9: Portfolio Packaging and Demo Readiness

### Task 25: Write final architecture and demo docs

**Files:**
- Modify: `README.md`
- Create: `docs/architecture/AI_PRODUCT_ARCHITECTURE.md`
- Create: `docs/eval/AI_PRODUCT_EVAL_SUMMARY.md`
- Create: `docs/demo/DEMO_SCRIPT.md`

**Step 1: Write the failing test**
- Add a docs check or manual acceptance checklist for the final repo narrative.

**Step 2: Run test to verify it fails**
- Run the docs check.
- Expected: missing final docs.

**Step 3: Write minimal implementation**
- Document setup, architecture, eval results, safety boundaries, and demo flow.

**Step 4: Run test to verify it passes**
- Run the docs check again.
- Expected: PASS.

**Step 5: Commit**
- `git add README.md docs/architecture/AI_PRODUCT_ARCHITECTURE.md docs/eval/AI_PRODUCT_EVAL_SUMMARY.md docs/demo/DEMO_SCRIPT.md`

### Task 26: Final verification pass

**Files:**
- No code changes expected unless failures appear.

**Step 1: Run the full verification set**
- Run:
  - `python -m pytest tests/eval -v`
  - `python -m compileall apps packages scripts/eval`
  - `npm --prefix frontend run lint`
  - `docker compose config`

**Step 2: Fix any failures**
- Only address real failures, not cosmetic noise.

**Step 3: Re-run verification**
- Expected: all checks pass.

**Step 4: Commit**
- Commit only if there were actual code/doc fixes in this phase.

---

## Execution Notes

- Keep every task small and shippable.
- Prefer one phase per commit series.
- Do not start the next phase until the previous phase passes its verification checks.
- Keep `civil_contract_dispute` as the primary case family until ingestion, retrieval, and eval are stable.
- Use `ref.md` as the shortlist for architecture study; do not copy repos blindly.
- Treat all LLM outputs as non-binding and review-gated.
