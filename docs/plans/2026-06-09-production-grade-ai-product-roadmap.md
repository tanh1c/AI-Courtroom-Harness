# Production-Grade AI Product Roadmap

Date: 2026-06-09
Project: AI Courtroom Harness
Target: AI Engineer portfolio, full-stack AI product, production-grade depth
Timeline: 6-9 months

## 1. Executive Summary

AI Courtroom Harness should evolve from a courtroom simulation demo into a production-grade AI legal workflow product. The final product should demonstrate document ingestion, retrieval grounding, agentic workflow orchestration, verification, human review, observability, evaluation, and an inspection-first frontend.

The goal is not to build a fake automated judge. The goal is to build a safe, auditable legal simulation and review system where every generated claim can be traced back to evidence, citations, model calls, and reviewer decisions.

A strong portfolio version should let an interviewer inspect:

- what documents were ingested,
- how they were parsed and chunked,
- which evidence spans support each claim,
- which legal citations were retrieved,
- what each agent/runtime node did,
- which guardrails fired,
- what the human reviewer approved or rejected,
- how the system performs on evaluation cases,
- and how the product behaves under failure or adversarial inputs.

## 2. Target Positioning

Recommended portfolio positioning:

> A production-grade AI legal workflow product for Vietnamese civil dispute simulation. It combines document ingestion, hybrid legal retrieval, graph-based agent orchestration, citation/evidence verification, human review, eval-driven guardrails, and an inspection UI that exposes the full reasoning and trace pipeline.

Avoid positioning it as:

- an AI judge,
- a legal advice product,
- a generic multi-agent chatbot,
- or a role-play courtroom toy.

The strongest story is: **safe, inspectable, eval-driven legal AI workflow engineering**.

## 3. Current-State Gaps

Based on the current repo state, the main gaps are:

1. **Runtime is still mostly heuristic.** V2 has a staged flow, but many utterances and decisions are deterministic templates. LLM usage is mostly optional polishing rather than meaningful graph-based reasoning.
2. **Retrieval is demo-grade.** BM25 plus optional Colab/ngrok vector retrieval is not enough for a production-grade RAG portfolio.
3. **Document ingestion is shallow.** PDF/text extraction exists, but there is no canonical document model, layout-aware parsing, OCR pipeline, or provenance-rich chunking.
4. **Evaluation is smoke-test-heavy.** Existing scripts are useful, but the repo needs real eval datasets, metrics, CI thresholds, and failure reports.
5. **Observability is missing.** There is no serious tracing for retrieval, LLM calls, guardrails, token/cost, latency, prompt versions, or reviewer actions.
6. **Human review is product-light.** Current review gates are useful as a concept, but need a queue, audit records, reviewer decisions, and UI inspection.
7. **Frontend is not yet an AI inspection console.** It looks like a product dashboard, but needs deeper views for claims, evidence, citations, traces, evals, and guardrails.
8. **Packaging/reproducibility need hardening.** Imports and setup should be cleaned so a reviewer can clone, install, run tests, and demo reliably.

## 4. Selected Reference Stack

The research in `ref.md` lists many good repos. The roadmap should stay selective and avoid framework sprawl.

### Primary references to study deeply

| Area | Primary reference | Why it matters |
| --- | --- | --- |
| Document parsing | `docling-project/docling` | Best reference for canonical document objects, page/block/table/provenance structure. |
| OCR pipeline | `ocrmypdf/OCRmyPDF` | Battle-tested OCR job pipeline and artifact handling. |
| Vector retrieval | `qdrant/qdrant` | Practical vector DB with metadata filtering, easier than Vespa for this portfolio. |
| Hybrid/RAG architecture | `infiniflow/ragflow`, `Azure-Samples/azure-search-openai-demo` | Strong product-level references for document RAG, citations, UI, and deployment patterns. |
| Agent graph | `langchain-ai/langgraph` | Best fit for graph/state/human-in-loop case workflow. |
| Typed AI outputs | `pydantic/pydantic-ai` | Useful reference for schema-first agent output and typed tools. |
| Evals | `confident-ai/deepeval`, `vibrantlabsai/ragas`, `promptfoo/promptfoo` | Good coverage across LLM/RAG regression, RAG metrics, and red-team style tests. |
| Observability | `langfuse/langfuse`, `arize-ai/phoenix` | Trace, prompt, eval dataset, and experiment workflows. |
| Human review | `HumanSignal/label-studio` | Reference for annotation/review queue patterns. |
| Safety/security | `microsoft/presidio`, `protectai/llm-guard`, `NVIDIA/garak`, `microsoft/PyRIT` | PII redaction, prompt-injection scanning, AI red-team testing. |

### Technologies to seriously consider using

| Layer | Recommended choice | Fallback / study-only |
| --- | --- | --- |
| Backend API | FastAPI | Keep current stack. |
| Database | PostgreSQL | SQLite only for local demo mode. |
| Vector DB | Qdrant | Vespa only if hybrid ranking becomes central and infra complexity is acceptable. |
| Document parsing | Docling | Unstructured for connector-heavy ingestion. |
| OCR | OCRmyPDF | PaddleOCR/Surya for layout-heavy scanned docs after license/performance review. |
| Agent workflow | LangGraph | PydanticAI for typed agent wrappers; Temporal later for durable background workflows. |
| Evaluation | DeepEval + RAGAS + Promptfoo | Inspect AI for research-style evals. |
| Observability | Langfuse | Phoenix if OpenTelemetry/eval loop is preferred. |
| PII/security | Presidio + LLM Guard | PyRIT/Garak for scheduled red-team runs. |
| Frontend | React/Vite + TanStack Query + shadcn/ui | Keep current frontend stack but split components and add inspection views. |
| Deployment | Docker Compose | Kubernetes is unnecessary for portfolio unless the product is already stable. |

## 5. Architecture Vision

Target architecture:

```text
User / Reviewer
    |
    v
React Inspection UI
    |
    v
FastAPI Backend
    |
    +--> Case Store / PostgreSQL
    +--> Artifact Store / local or object storage
    +--> Document Ingestion Pipeline
    |       +--> PDF parse / OCR
    |       +--> canonical document object
    |       +--> chunks with page/block/span provenance
    |
    +--> Retrieval Layer
    |       +--> BM25 keyword retrieval
    |       +--> Qdrant dense retrieval
    |       +--> reranker
    |       +--> citation verifier
    |
    +--> LangGraph Case Workflow
    |       +--> intake node
    |       +--> retrieval node
    |       +--> claim drafting node
    |       +--> plaintiff/defense/judge nodes
    |       +--> fact-check node
    |       +--> citation verification node
    |       +--> human review node
    |       +--> report writer node
    |
    +--> Evaluation Harness
    |       +--> retrieval metrics
    |       +--> grounding metrics
    |       +--> safety metrics
    |       +--> regression reports
    |
    +--> Observability
            +--> traces
            +--> model/prompt versions
            +--> latency/token/cost
            +--> eval scores
```

The frontend should become an inspection console, not just a courtroom visualization layer.

## 6. Roadmap Overview

### Phase 1 — Foundation and Reproducibility

Duration: 3-4 weeks

Goal: make the repo clean, reproducible, and credible before adding more AI complexity.

#### Workstreams

1. **Packaging cleanup**
   - Fix Python package discovery so `shared`, `retrieval`, `orchestration`, `verification`, and `reporting` install cleanly.
   - Remove reliance on `sys.path` hacks where possible.
   - Standardize imports.

2. **Environment setup**
   - Add one canonical setup path for Windows/local development.
   - Add `.env.example`.
   - Add reproducible smoke test commands.
   - Make it clear which Python interpreter is required.

3. **Testing baseline**
   - Convert smoke scripts into a clearer test/eval structure.
   - Add a single command for backend checks.
   - Keep existing smoke scripts but separate them from production evals.

4. **Frontend maintainability**
   - Split the large app file into mode panels, shared layout, API hooks, and inspection components.
   - Do not redesign the UI yet; only make it maintainable.

#### Acceptance criteria

- Fresh clone can install and run backend/frontend.
- Python package imports work without fragile path assumptions.
- Frontend typecheck passes.
- Backend smoke tests pass under the documented venv.
- README has a reliable local run path.

#### Reference repos

- Azure Search OpenAI Demo for repo discipline, infra, and full-stack shape.
- Haystack RAG app for a minimal FastAPI + RAG product skeleton.

## 7. Phase 2 — Document Ingestion and Provenance

Duration: 4-6 weeks

Goal: replace shallow parsing with a production-style document pipeline.

#### Workstreams

1. **Canonical document model**
   - Introduce structured document artifacts:
     - `document_id`
     - `case_id`
     - `page_number`
     - `block_id`
     - `block_type`
     - `text`
     - `bbox` when available
     - `source_uri`
     - `checksum`
     - `parser_version`
     - `confidence`
   - Store parsed artifacts separately from case summaries.

2. **PDF parsing**
   - Evaluate Docling as primary parser.
   - Keep PyMuPDF/pypdf only as fallback or simple parser path.
   - Preserve page/block provenance.

3. **OCR pipeline**
   - Add OCRmyPDF as an async/background job path for scanned PDFs.
   - Store OCR output as a generated artifact.
   - Track OCR confidence and warnings.

4. **Chunking with provenance**
   - Chunk by document structure, not blind character windows.
   - Every chunk must reference source page/block/span.
   - Add chunk checksum/versioning.

5. **Parser evaluation**
   - Build a small document ingestion eval set:
     - clean PDF,
     - scanned PDF,
     - contract-like document,
     - receipt/payment evidence,
     - message/chat evidence,
     - malformed/low-quality scan.

#### Acceptance criteria

- The system can show exactly where each extracted fact came from.
- OCR and parser warnings are visible in backend state and UI.
- Ingestion artifacts are replayable and versioned.
- The UI can display document chunks and source provenance.

#### Reference repos

- Docling: canonical document model and layout-aware conversion.
- OCRmyPDF: idempotent OCR pipeline and artifact generation.
- Unstructured: partition-clean-chunk-metadata-index pattern.
- Marker/Surya: study only for layout-aware ideas; avoid direct dependency until license risks are clear.

## 8. Phase 3 — Retrieval, RAG, and Citation Grounding

Duration: 6-8 weeks

Goal: make retrieval measurable, hybrid, and defensible.

#### Workstreams

1. **Hybrid retrieval layer**
   - Keep BM25 for lexical legal retrieval.
   - Add Qdrant for dense vector retrieval.
   - Add metadata filters:
     - jurisdiction,
     - document type,
     - legal domain,
     - effective status,
     - source type,
     - page range.

2. **Reranking**
   - Add a reranker experiment path.
   - Candidate references:
     - BGE reranker via FlagEmbedding,
     - cross-encoder reranker,
     - or provider-based reranking if cost is acceptable.

3. **Citation provenance**
   - Every citation should include:
     - source document,
     - article/clause,
     - effective status,
     - retrieval score,
     - rerank score,
     - source span if available.

4. **Legal retrieval eval set**
   - Build gold queries for `civil_contract_dispute` first.
   - Track expected citations and acceptable alternatives.
   - Metrics:
     - recall@k,
     - precision@k,
     - MRR,
     - nDCG,
     - citation validity.

5. **Grounding API**
   - Add a claim-to-evidence/citation grounding service.
   - Distinguish:
     - supported,
     - weakly supported,
     - unsupported,
     - contradicted,
     - citation expired/invalid.

#### Acceptance criteria

- Retrieval quality is measured, not guessed.
- Claims can be mapped to evidence and citation IDs.
- The UI can show why a claim is grounded or ungrounded.
- CI can fail if retrieval quality regresses below threshold.

#### Reference repos

- Qdrant: vector DB and metadata filtering.
- Vespa sample-apps: hybrid ranking and RRF/ColBERT concepts.
- RAGFlow: product-level document RAG patterns.
- Azure Search OpenAI Demo: citation UI and thought-process/source display.
- BEIR: retrieval metric structure.
- RAGAS: RAG eval metrics.

## 9. Phase 4 — Graph-Based Agent Runtime

Duration: 6-8 weeks

Goal: turn the current staged simulator into a traceable graph workflow.

#### Workstreams

1. **Graph design**
   - Introduce a LangGraph-based workflow:
     - case intake,
     - document ingest,
     - retrieval,
     - issue framing,
     - plaintiff position,
     - defense position,
     - judge questioning,
     - fact check,
     - citation verification,
     - decision guard,
     - human review,
     - report export.

2. **Typed node contracts**
   - Every node should define:
     - input schema,
     - output schema,
     - tools allowed,
     - retry/fallback behavior,
     - trace metadata.

3. **Separate generation from policy**
   - LLMs can draft or summarize.
   - Deterministic services enforce:
     - citation validity,
     - official-language blocking,
     - evidence support,
     - human review requirements.

4. **Tool call discipline**
   - Tools should be explicit:
     - retrieve legal citations,
     - fetch evidence chunk,
     - verify citation,
     - check grounding,
     - create report.

5. **Replay mode**
   - Add deterministic replay from saved model outputs and retrieval results.
   - Useful for demos, debugging, and eval regression.

#### Acceptance criteria

- The system has a real workflow graph, not only hardcoded stage methods.
- Each step is inspectable in the UI.
- LLM outputs are schema-validated.
- Failed guardrails route to review instead of silently continuing.
- A saved run can be replayed or inspected.

#### Reference repos

- LangGraph: state, checkpointing, human-in-loop, graph workflows.
- PydanticAI: typed outputs and schema-first agent behavior.
- OpenAI Agents SDK: trace/tool/handoff patterns to study, not necessarily adopt directly.
- Temporal samples: study for future durable long-running jobs, not mandatory in the first production-grade milestone.

## 10. Phase 5 — Evaluation Harness and Quality Gates

Duration: 5-7 weeks

Goal: build evals that prove the product is reliable and safe enough for portfolio scrutiny.

#### Workstreams

1. **Eval dataset structure**
   - Store eval cases as versioned JSON/JSONL.
   - Include:
     - input documents,
     - expected extracted facts,
     - expected citations,
     - expected guardrail decisions,
     - expected human review status,
     - expected report constraints.

2. **Retrieval eval**
   - Measure recall@k, nDCG, MRR.
   - Track citation correctness and effective-status correctness.

3. **Grounding eval**
   - Check whether generated claims cite valid evidence/citation.
   - Measure unsupported claim rate.
   - Measure contradiction detection.

4. **Safety eval**
   - Add adversarial cases:
     - prompt injection inside uploaded document,
     - fake legal article,
     - expired citation,
     - official judgment wording,
     - unsupported remedy,
     - PII-heavy document,
     - conflicting evidence.

5. **Agent workflow eval**
   - Check graph transitions.
   - Check required nodes run.
   - Check human review gate behavior.
   - Check report export constraints.

6. **CI quality gates**
   - Add thresholds for smoke and regression evals.
   - Keep expensive evals optional or scheduled.

#### Acceptance criteria

- Eval reports are generated as JSON and human-readable HTML/Markdown.
- CI runs a small deterministic eval suite.
- Failed traces can become new eval cases.
- The README can show current eval scores honestly.

#### Reference repos

- DeepEval: pytest-style LLM/RAG/agent regression tests.
- RAGAS: RAG metrics.
- Promptfoo: prompt/model/version matrices and red-team regression.
- Inspect AI: structured eval task/solver/scorer design.
- OpenAI Evals: eval registry ideas.

## 11. Phase 6 — Observability, Audit, and Human Review

Duration: 5-7 weeks

Goal: make the product inspectable like a real AI system.

#### Workstreams

1. **Run tracing**
   - Add a `run_id` for every case workflow.
   - Trace:
     - ingestion steps,
     - retrieval queries/results,
     - LLM calls,
     - prompt versions,
     - tool calls,
     - guardrail decisions,
     - human review events.

2. **Token/cost/latency tracking**
   - Track provider/model, latency, tokens, estimated cost.
   - Surface this in a run summary.

3. **Prompt/version registry**
   - Store prompt templates with version IDs.
   - Link every LLM output to prompt version and model version.

4. **Human review audit model**
   - Add review records:
     - reviewer,
     - timestamp,
     - decision,
     - notes,
     - evidence spans reviewed,
     - citations approved/rejected,
     - final status.

5. **PII and sensitive data handling**
   - Add PII detection/redaction flow for logs/traces.
   - Never log raw legal documents into external observability by default.

#### Acceptance criteria

- A reviewer can inspect a full run trace end-to-end.
- Every report has an audit trail.
- Human review decisions are stored as first-class artifacts.
- Sensitive text logging is controlled and documented.

#### Reference repos

- Langfuse: traces, prompts, scores, datasets.
- Phoenix: trace-to-dataset-to-eval loop.
- Label Studio: review/annotation queue patterns.
- Presidio: PII detection and anonymization.
- LLM Guard: input/output scanning.

## 12. Phase 7 — Product UI as AI Inspection Console

Duration: 6-8 weeks

Goal: make the frontend demonstrate AI engineering depth, not just visual polish.

#### Workstreams

1. **Case workspace redesign**
   - Keep courtroom timeline, but make it secondary to inspection.
   - Main panels:
     - documents,
     - extracted facts,
     - evidence map,
     - retrieval results,
     - claims,
     - citations,
     - agent trace,
     - guardrails,
     - human review,
     - final report.

2. **Document source viewer**
   - Show page/block/chunk provenance.
   - Highlight evidence spans used by claims.

3. **Claim grounding view**
   - For each claim, show:
     - evidence support,
     - citation support,
     - confidence,
     - verifier notes,
     - reviewer status.

4. **Trace viewer**
   - Show graph nodes and step outputs.
   - Let users inspect model input/output in redacted form.
   - Show token/cost/latency.

5. **Eval dashboard**
   - Show latest eval run:
     - retrieval scores,
     - grounding scores,
     - safety failures,
     - regression status.

6. **Human review queue**
   - Add approve/reject/request-more-evidence actions.
   - Reviewer decisions should update audit state.

#### Acceptance criteria

- The UI can explain why the system produced a report.
- A portfolio reviewer can click from final conclusion back to source evidence.
- Eval and trace results are visible without reading logs.
- The product feels like a professional AI workflow tool, not a static demo.

#### Reference repos

- Azure Search OpenAI Demo: citation panel and thought-process UI.
- RAGFlow: document RAG product layout and source display.
- Dify: workflow UI concepts, not the no-code abstraction.
- Open WebUI: admin/permissions/knowledge-base patterns to study carefully.

## 13. Phase 8 — Security, Deployment, and Hardening

Duration: 4-6 weeks

Goal: make the final repo credible as a production-grade portfolio artifact.

#### Workstreams

1. **File upload security**
   - Validate file types and sizes.
   - Store uploads safely.
   - Avoid path traversal risks.
   - Scan or sandbox parsing where possible.

2. **Prompt injection defense**
   - Add tests where uploaded documents contain malicious instructions.
   - Ensure document text is treated as data, not system instruction.

3. **PII protection**
   - Add redaction/anonymization path for logs and traces.
   - Document what is stored locally and externally.

4. **Auth and roles**
   - Add minimal local auth or role simulation:
     - admin,
     - reviewer,
     - analyst.
   - If full auth is too much, clearly scope it as local demo mode.

5. **Docker Compose**
   - Services:
     - API,
     - frontend,
     - PostgreSQL,
     - Qdrant,
     - optional Langfuse/Phoenix.

6. **CI**
   - Lint/typecheck.
   - Backend tests.
   - Deterministic eval smoke.
   - Security/adversarial smoke.

7. **Portfolio documentation**
   - Architecture diagram.
   - System design write-up.
   - Eval report snapshot.
   - Demo script.
   - Failure modes and limitations.

#### Acceptance criteria

- `docker compose up` can run a local demo stack.
- CI proves the system is not just locally lucky.
- Security limitations are documented honestly.
- The final README is portfolio-grade and concise.

#### Reference repos

- OWASP LLM Top 10: threat model checklist.
- Presidio: PII protection.
- LLM Guard: prompt/input/output scanners.
- PyRIT/Garak/Promptfoo: red-team regression tests.
- Langfuse/Docker examples: observability deployment.

## 14. Month-by-Month Timeline

### Month 1 — Repo hardening and architecture reset

Deliverables:

- Clean package structure.
- Reliable local setup.
- Test command baseline.
- Initial architecture diagram.
- Frontend component split.
- Roadmap converted into tracked implementation plan.

Portfolio value:

- Shows engineering discipline.
- Removes prototype smell.

### Month 2 — Document ingestion foundation

Deliverables:

- Canonical document model.
- Docling parser experiment.
- OCRmyPDF pipeline experiment.
- Document artifacts with provenance.
- Ingestion UI/source viewer prototype.

Portfolio value:

- Shows real document AI engineering.

### Month 3 — Hybrid retrieval and citation grounding

Deliverables:

- Qdrant integration.
- Hybrid BM25 + dense retrieval.
- Metadata filters.
- First retrieval eval dataset.
- Citation/evidence grounding service.

Portfolio value:

- Shows RAG depth beyond vector search.

### Month 4 — Agent graph runtime

Deliverables:

- LangGraph workflow skeleton.
- Typed node contracts.
- Tool-call trace structure.
- Deterministic replay mode.
- V2 flow migrated or wrapped into graph runtime.

Portfolio value:

- Shows agentic orchestration with engineering discipline.

### Month 5 — Evaluation harness

Deliverables:

- DeepEval/RAGAS/Promptfoo evaluation structure.
- Retrieval, grounding, safety, and workflow evals.
- JSON/Markdown eval reports.
- CI smoke eval threshold.

Portfolio value:

- Shows production-grade AI quality control.

### Month 6 — Observability and human review

Deliverables:

- Langfuse or Phoenix integration.
- Prompt/model/run trace records.
- Token/cost/latency logging.
- Human review audit model.
- Review queue UI.

Portfolio value:

- Shows inspectability and operational maturity.

### Month 7 — Inspection UI upgrade

Deliverables:

- Claim grounding view.
- Citation provenance view.
- Trace viewer.
- Eval dashboard.
- Report audit trail.

Portfolio value:

- Shows full-stack AI product quality.

### Month 8 — Security and deployment

Deliverables:

- Docker Compose stack.
- Prompt injection tests.
- PII redaction path.
- File upload hardening.
- CI security/eval smoke.

Portfolio value:

- Shows production readiness.

### Month 9 — Polish and portfolio packaging

Deliverables:

- Final README.
- Architecture docs.
- Demo video/script.
- Public eval report snapshot.
- Case study write-up.
- Known limitations section.

Portfolio value:

- Makes the project easy to evaluate by recruiters and senior engineers.

## 15. Production-Grade Acceptance Criteria

The project is portfolio-ready only when these are true:

### Reproducibility

- Fresh clone works with documented setup.
- Local demo can run through Docker Compose or clear venv/npm steps.
- Tests and eval smoke commands are documented.

### Ingestion

- Documents produce structured artifacts.
- Chunks preserve source provenance.
- OCR warnings/confidence are visible.

### Retrieval

- Hybrid retrieval is implemented.
- Retrieval eval metrics are tracked.
- Citation source and effective status are visible.

### Agent workflow

- Runtime is graph-based or graph-wrapped.
- Each node has typed inputs/outputs.
- Tool calls are traceable.
- Replay mode exists.

### Verification

- Unsupported claims are detected.
- Invalid/expired citations are flagged.
- Official-judgment wording is blocked.
- Prompt injection cases are tested.

### Human review

- Reviewer actions are stored.
- Reports cannot hide unresolved review blockers.
- Audit trail links reviewer decisions to evidence/citations.

### Observability

- LLM/retrieval/guardrail traces exist.
- Latency/token/cost are tracked.
- Prompt/model versions are recorded.

### Frontend

- UI supports source-to-claim-to-report inspection.
- Trace and eval views exist.
- Human review workflow is usable.

### Documentation

- README explains product, architecture, limitations, setup, and demo.
- Architecture diagram is current.
- Eval report is included.
- Known limitations are honest.

## 16. What to Remove or De-emphasize

To avoid a bloated portfolio project, remove or de-emphasize:

1. **MVP/V1 clutter in the main UI.** Keep them as historical notes or developer-only modes.
2. **Colab/ngrok vector retrieval as a core feature.** It can stay as an old experiment, but not as the production path.
3. **Hardcoded courtroom dialogue as the main AI story.** Keep deterministic fallback, but do not sell it as agentic reasoning.
4. **Manual model benchmark notes as the main evaluation.** Replace with executable eval harnesses.
5. **Provider sprawl.** Keep a clean provider abstraction; do not make the roadmap about trying every model.
6. **Placeholder workspaces.** Remove or clearly label unused `apps/web`-style placeholders.
7. **UI polish without AI inspection depth.** Visual polish matters, but only after trace/eval/grounding are strong.

## 17. Suggested Final Demo Flow

A strong final demo should run like this:

1. User uploads a contract dispute case with PDF evidence.
2. Ingestion pipeline parses the document, OCRs if needed, and creates source-linked chunks.
3. Retrieval finds relevant legal citations using hybrid search.
4. Agent graph runs the case workflow.
5. The system drafts positions, questions, and a non-binding simulated outcome.
6. Verification flags unsupported claims, citation issues, and review blockers.
7. Human reviewer approves, rejects, or requests more evidence.
8. Final report exports with citations, evidence links, trace metadata, and disclaimers.
9. UI shows the full path from final conclusion back to document spans and legal citations.
10. Eval dashboard shows how this run compares to regression benchmarks.

This demo tells a much stronger AI Engineer story than simply showing a courtroom transcript.

## 18. Suggested Final README Narrative

Final README should open with something like:

> AI Courtroom Harness is a production-grade AI legal workflow simulator for Vietnamese civil disputes. It ingests legal documents, extracts evidence with provenance, performs hybrid legal retrieval, orchestrates a graph-based case workflow, verifies claim/citation grounding, routes risky outputs through human review, and exposes every step through an inspection UI and eval harness.

Then show:

- architecture diagram,
- quickstart,
- demo screenshots,
- eval summary,
- safety boundaries,
- tech stack,
- limitations.

## 19. Key Risks

| Risk | Mitigation |
| --- | --- |
| Framework sprawl | Use a small primary stack: FastAPI, React, Docling, Qdrant, LangGraph, DeepEval, Langfuse, Presidio. |
| Legal correctness overclaim | Keep all output non-binding and human-review-gated. |
| RAG quality remains weak | Build retrieval eval before expanding case families. |
| UI consumes too much time | Build inspection UI incrementally from backend artifacts. |
| LLM-as-judge becomes unreliable | Calibrate with gold cases and human labels. |
| Observability leaks sensitive text | Add redaction and local-only tracing defaults. |
| Product becomes too broad | Focus first on `civil_contract_dispute`; expand later only after core quality is proven. |

## 20. Recommended Implementation Order

If time becomes limited, prioritize in this exact order:

1. Reproducible setup and package cleanup.
2. Canonical document model and provenance.
3. Hybrid retrieval and citation grounding.
4. Eval harness with regression thresholds.
5. Graph-based runtime and trace structure.
6. Inspection UI for source/claim/citation/trace.
7. Human review audit workflow.
8. Security hardening and Docker Compose.
9. Final portfolio docs and demo script.

Do not start with UI redesign. The product will look better but remain technically shallow. The backend artifacts and evals must come first, then the UI should expose them.
