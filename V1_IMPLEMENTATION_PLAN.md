# AI Courtroom Harness V1 Implementation Plan

This plan starts **after the MVP frontend is complete** and `Milestone F` is closed.

The MVP proves the core harness path. V1 expands it into a fuller courtroom-simulation harness with clearer procedure, explicit verification agents, evidence challenge flow, and a non-binding proposed outcome.

## 0. Progress Snapshot

- [x] V1 Phase 0 contract expansion is complete.
- [x] Python Pydantic schemas include the V1 hearing session surface.
- [x] TypeScript shared types mirror the V1 schema surface.
- [x] A complete V1 hearing session fixture exists.
- [x] Migration notes explain how V1 extends MVP contracts without breaking current flows.
- [x] V1 Phase 1 procedural runtime is complete with stage-based start, advance, guard, and persistence.
- [x] V1 Phase 2 evidence and verification agents are complete with explicit turns, tool traces, challenge endpoint, and verification endpoint.
- [x] V1 Phase 3 clarification round is complete with multi-question judge clarification, grounded party responses, and unresolved-question review checklist propagation.
- [ ] V1 report/UI integration has not started.

## 1. V1 Decision

V1 scope:

- Build a **Full Courtroom Simulation Harness** for `civil_contract_dispute`.
- Keep the system as legal education, simulation, and decision-support.
- Add richer hearing procedure and traceability.
- Add a controlled, non-binding proposed outcome.

V1 must not become an automated judge.

## 2. Product Boundary

### In Scope

- Stage-based simulated hearing flow.
- Explicit `Evidence Agent`, `Fact-check Agent`, and `Citation Verifier Agent` turns.
- Role permission checks per hearing stage.
- Evidence challenge and admissibility status.
- Judge clarification questions and party responses.
- Non-binding proposed outcome candidates.
- Stronger report format for a simulated hearing record.
- Three stable demo cases for evaluation.

### Out Of Scope

- Official legal judgment or automated verdict.
- Criminal, land, family, or administrative case types.
- Production authentication and RBAC.
- Real-time multi-user collaboration.
- Fine-tuning LLMs.
- Heavy OCR or production document AI.
- Full court-agency workflow.

## 3. Target V1 User Journey

```text
Create or upload case
-> Parse facts, evidence, and legal issues
-> Open simulated hearing
-> Mở phiên
-> Evidence Agent presents evidence registry
-> Legal Retrieval Agent retrieves legal basis
-> Nguyên đơn trình bày
-> Bị đơn đối đáp
-> Evidence challenge round
-> Judge clarification questions
-> Party responses
-> Fact-check Agent validates claims
-> Citation Verifier checks legal basis
-> Judge gives non-binding preliminary assessment
-> Human review
-> Clerk exports formal simulated hearing record
```

## 4. Core V1 Modules

### V1-M1. Expanded Shared Contracts

Status:

- [x] Completed for V1 Phase 0

Add schemas for:

- `HearingStage`
- `HearingSession`
- `RolePermission`
- `EvidenceChallenge`
- `EvidenceAdmissibility`
- `ClarificationQuestion`
- `PartyResponse`
- `OutcomeCandidate`
- `AgentToolCall`
- `HarnessViolation`

Acceptance:

- [x] Python and TypeScript contracts stay aligned.
- [x] Fixtures include at least one complete V1 hearing session.
- [x] Existing MVP fixtures remain compatible or have migration notes.

### V1-M2. Stage-Based Courtroom Runtime

Status:

- [x] Completed for V1 Phase 1

Replace the current mostly linear runtime with stage-aware orchestration:

- `OPENING`
- `EVIDENCE_PRESENTATION`
- `LEGAL_RETRIEVAL`
- `PLAINTIFF_ARGUMENT`
- `DEFENSE_ARGUMENT`
- `EVIDENCE_CHALLENGE`
- `JUDGE_QUESTIONS`
- `PARTY_RESPONSES`
- `FACT_CHECK`
- `CITATION_VERIFICATION`
- `PRELIMINARY_ASSESSMENT`
- `HUMAN_REVIEW`
- `CLOSING_RECORD`

Acceptance:

- [x] Every agent turn has a `hearing_stage`.
- [x] Turn order is enforced by the runtime.
- [x] Invalid agent-stage combinations are rejected or flagged.

### V1-M3. Role Permission Manager

Status:

- [ ] Planned

Add a small policy layer that answers:

- Which agent may speak in this stage?
- Which evidence can this agent use?
- Which citations can this agent use?
- Does this claim require evidence, citation, or both?
- Should this output be blocked, repaired, or sent to human review?

Acceptance:

- [ ] Plaintiff and defense cannot speak outside allowed stages.
- [ ] Judge cannot invent facts not present in case state.
- [ ] Clerk can summarize but cannot create new claims.
- [ ] Permission failures are written to audit trail.

### V1-M4. Evidence Agent And Challenge Flow

Status:

- [x] Completed for V1 Phase 2

Add explicit evidence handling:

- Evidence Agent summarizes all evidence.
- Evidence gets `admitted`, `disputed`, `rejected`, or `needs_review`.
- Plaintiff and defense can challenge evidence.
- Challenge reasons are persisted and visible in the report/UI.

Acceptance:

- [x] Each evidence item has status and source.
- [x] Each challenge records party, reason, and affected claim IDs.
- [x] Disputed evidence raises review priority.

### V1-M5. Explicit Verification Agents

Status:

- [x] Completed for V1 Phase 2

Promote current backend checks into visible transcript turns:

- Fact-check Agent turn.
- Citation Verifier Agent turn.
- Unsupported claim report.
- Citation mismatch report.
- Contradiction report.

Acceptance:

- [x] Verification results appear in transcript and V1 verification API response.
- [x] Invalid/expired citation IDs are separated before V1 finalization.
- [x] Unsupported claims are visible to human reviewer through `fact_check` and verification turns.

### V1-M6. Clarification Round

Status:

- [x] Completed for V1 Phase 3

Add judge-led clarification:

- Judge asks targeted questions.
- Plaintiff responds.
- Defense responds.
- Unresolved questions remain attached to final report.

Acceptance:

- [x] At least two judge questions are generated when risk is medium or high.
- [x] Each response must cite evidence/citation or explicitly say evidence/citation is missing.
- [x] Unanswered questions are carried into human review checklist.

### V1-M7. Non-Binding Proposed Outcome

Status:

- [ ] Planned

Add cautious outcome candidates:

- `likely_plaintiff_favored`
- `likely_defense_favored`
- `split_or_uncertain`
- `requires_more_evidence`

Each candidate must include:

- rationale
- supported claim IDs
- evidence IDs
- citation IDs
- risk level
- disclaimer

Acceptance:

- [ ] Outcome is clearly labeled non-binding.
- [ ] Outcome cannot be exported without human review.
- [ ] No official judgment language such as "the court orders" or "the court hereby decides".

### V1-M8. Formal Hearing Record Report

Status:

- [ ] Planned

Upgrade report output into a fuller simulated hearing record:

- case metadata
- procedural timeline
- evidence registry
- evidence challenges
- party arguments
- judge questions and responses
- verification agent findings
- human review decision
- non-binding proposed outcome
- disclaimer

Acceptance:

- [ ] Markdown and HTML preview both render the V1 sections.
- [ ] Report remains readable without the frontend.
- [ ] Rejected citations are not shown as valid legal basis.

### V1-M9. Evaluation And Demo Cases

Status:

- [ ] Planned

Create a small V1 evaluation set:

- `demo_contract_delivery_delay`
- `demo_payment_condition_dispute`
- `demo_defective_goods_dispute`

Each case should include:

- narrative
- attachment fixture
- expected legal issues
- expected evidence statuses
- expected verification flags

Acceptance:

- [ ] At least three demo cases run end-to-end.
- [ ] Smoke script validates V1 stage order.
- [ ] Negative tests cover unsupported claims, invalid citations, and role violations.

## 5. V1 Phases

### V1 Phase 0. Contract Expansion

Goal:

- Freeze the V1 schemas before implementation.

Tasks:

- [x] Add new Pydantic schemas.
- [x] Mirror TypeScript types.
- [x] Add V1 fixture shape.
- [x] Add migration notes for MVP outputs.

Exit criteria:

- [x] V1 fixture validates against the Python source of truth, and TypeScript mirror types are available for frontend work.

### V1 Phase 1. Procedural Runtime

Goal:

- Replace linear courtroom flow with stage-based orchestration.

Tasks:

- [x] Add `HearingSession`.
- [x] Add stage enum and transition table.
- [x] Add runtime guard for invalid turn order.
- [x] Persist stage-by-stage transcript.

Exit criteria:

- [x] One demo case runs through all V1 stages.

### V1 Phase 2. Evidence And Verification Agents

Goal:

- Make evidence and verification visible as first-class agent turns.

Tasks:

- [x] Add Evidence Agent.
- [x] Add evidence challenge round.
- [x] Add explicit Fact-check Agent turn.
- [x] Add explicit Citation Verifier Agent turn.

Exit criteria:

- [x] API exposes evidence challenges and verification agent turns through dedicated V1 endpoints.

Note:

- Full V1 hearing-record rendering remains in V1 Phase 5 with the report/UI hooks.

### V1 Phase 3. Clarification Round

Goal:

- Make judge questions and party responses part of the simulation.

Tasks:

- [x] Add judge clarification prompts.
- [x] Add party response turns.
- [x] Add unresolved question tracking.
- [x] Push unresolved questions into human review checklist.

Exit criteria:

- [x] Medium-risk cases produce clarification questions and party responses.

### V1 Phase 4. Proposed Outcome

Goal:

- Add a controlled, non-binding proposed outcome.

Tasks:

- [ ] Add `OutcomeCandidate` schema.
- [ ] Add outcome generation prompt and fallback.
- [ ] Add outcome verification guard.
- [ ] Add human review requirement.

Exit criteria:

- [ ] Outcome candidate exists only as reviewed decision-support, not a verdict.

### V1 Phase 5. Report, UI Hooks, And Evaluation

Goal:

- Make V1 demoable and measurable.

Tasks:

- [ ] Update markdown report renderer.
- [ ] Update HTML preview renderer.
- [ ] Expose V1 API response fields for frontend.
- [ ] Add three demo cases.
- [ ] Add V1 smoke and negative tests.

Exit criteria:

- [ ] V1 scripted demo runs end-to-end.
- [ ] V1 frontend can display hearing stages, challenges, verification turns, and proposed outcome.

## 6. Parallel Work Lanes

| Lane | Scope | Can Start After | Notes |
| --- | --- | --- | --- |
| Contracts | V1 schemas and fixtures | V1 Phase 0 | Blocks most other lanes |
| Runtime | Stage-based LangGraph flow | V1 schemas draft | Owns hearing order |
| Evidence | Evidence Agent and challenge flow | Evidence schemas | Keep CPU-friendly |
| Verification | Fact-check and citation turns | Runtime stages draft | Reuse existing verification service |
| Reporting | Markdown and HTML hearing record | V1 fixture draft | Can work from fixture first |
| Frontend | V1 UI surfaces | V1 API/fixture draft | Should not block backend |
| Evaluation | Demo cases and negative tests | V1 fixture draft | Start early |

## 7. API Additions To Consider

These endpoints are candidates, not final contracts:

- `POST /api/v1/cases/{case_id}/hearing/start`
- `POST /api/v1/cases/{case_id}/hearing/advance`
- `GET /api/v1/cases/{case_id}/hearing`
- `GET /api/v1/cases/{case_id}/evidence/challenges`
- `GET /api/v1/cases/{case_id}/verification`
- `GET /api/v1/cases/{case_id}/outcome`

Prefer extending existing endpoints if that keeps the API simpler.

## 8. V1 Definition Of Done

V1 is complete when:

- [ ] A case runs through a full stage-based simulated hearing.
- [ ] Evidence challenge flow is visible and persisted.
- [ ] Fact-check and citation verification are explicit transcript turns.
- [ ] Judge clarification questions and party responses are captured.
- [ ] Non-binding proposed outcome is generated only with grounding and review.
- [ ] Formal hearing record report includes all major stages.
- [ ] At least three demo cases pass smoke checks.
- [ ] Frontend can inspect all new V1 surfaces.

## 9. Risks And Guardrails

### Risk 1. The system sounds like it is issuing a judgment

Guardrail:

- Use "non-binding proposed outcome", "preliminary assessment", and "decision-support" wording.
- Avoid official judgment verbs in prompts and reports.

### Risk 2. More stages increase hallucination surface

Guardrail:

- Require evidence or citation references for every important claim.
- Push missing support into human review.

### Risk 3. V1 becomes too broad

Guardrail:

- Keep only `civil_contract_dispute`.
- Add more procedural depth before adding more legal domains.

### Risk 4. Frontend and backend drift

Guardrail:

- Use shared TypeScript types and V1 fixtures.
- Build UI from fixtures while backend endpoints stabilize.

## 10. Recommended First Step

Start with V1 Phase 0:

- Add the V1 shared schemas.
- Create one complete V1 fixture.
- Update the report renderer from that fixture before changing runtime.

This gives every lane a stable target before deeper implementation begins.
