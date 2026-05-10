# AI Courtroom Harness V2 Implementation Plan

V2 starts after the backend MVP and V1 procedural harness are stable. The goal is to make the output read and behave like a complete simulated civil hearing, while preserving the project boundary: this is an educational and decision-support simulation, not an official court judgment.

## 0. Progress Snapshot

- [x] V2 Phase 0 trial-flow contracts are defined.
- [x] V2 Phase 1 full trial procedure runtime is implemented.
- [x] V2 Phase 2 courtroom dialogue layer is implemented.
- [x] V2 Phase 3 deliberation and simulation-safe verdict guard is implemented.
- [x] V2 Phase 4 formal trial record and simulated outcome export are implemented.
- [x] V2 Phase 5 backend evaluation, demo fixtures, and API UI hooks are implemented.
- [x] Real frontend rendering and frontend handoff notes are complete in `frontend/`.

## 1. V2 Product Goal

V2 should generate a complete, formal, Vietnamese courtroom-style simulation for `civil_contract_dispute` cases:

```text
Prepare case
-> Open hearing
-> Clerk calls the case and records appearances
-> Judge explains scope and procedure
-> Plaintiff presents claims
-> Defense responds
-> Court examines evidence
-> Judge questions parties
-> Parties debate and rebut
-> Final statements
-> Deliberation break
-> Simulated decision or no-decision outcome
-> Clerk closes the record
```

The system may produce a **simulated non-binding decision** at the end of the demo flow. Human review is optional in V2 demo mode: unresolved evidence, weak citations, or risky claims should not block the transcript, but they must be surfaced in the risk notes, reviewer checklist, and simulated outcome rationale.

## 2. Product Boundary

### In Scope

- Full civil-hearing narrative from opening to closing.
- Formal Vietnamese labels and transcript sections.
- Multi-turn judge, plaintiff, defense, clerk, evidence, fact-check, and citation-verifier dialogue.
- Courtroom procedure stages, not only backend harness stages.
- Evidence examination and party rebuttal rounds.
- Deliberation summary with strict grounding.
- Simulated outcome guarded by evidence and citation checks, with optional human review notes.
- HTML and Markdown exports that resemble court minutes.

### Out Of Scope

- Official judgment generation.
- Real court filing workflow.
- Production legal advice.
- Criminal, family, land, or administrative procedure.
- Real-time multi-user courtroom UI.
- Fine-tuning or GPU-heavy training.

## 3. Core V2 Modules

### V2-M1. Trial Flow Contracts

Status:

- [x] Completed for V2 Phase 0

Add shared Python and TypeScript contracts for:

- `TrialProcedureStage`
- `CourtroomDialogueTurn`
- `ProceduralAct`
- `AppearanceRecord`
- `EvidenceExamination`
- `DebateRound`
- `FinalStatement`
- `DeliberationRecord`
- `SimulatedDecision`
- `DecisionGuardResult`

Acceptance:

- [x] Contracts support a complete hearing timeline.
- [x] Existing V1 `HearingSession` remains backward compatible.
- [x] Fixtures include one complete V2 trial transcript.

### V2-M2. Full Trial Procedure Runtime

Status:

- [x] Completed for V2 Phase 1

Expand the runtime from V1 technical stages into courtroom-facing stages:

- `case_preparation`
- `opening_formalities`
- `appearance_check`
- `procedure_explanation`
- `plaintiff_claim_statement`
- `defense_response_statement`
- `evidence_examination`
- `judge_examination`
- `plaintiff_debate`
- `defense_rebuttal`
- `final_statements`
- `deliberation`
- `simulated_decision`
- `closing_record`

Acceptance:

- [x] Runtime enforces stage order.
- [x] Each stage has allowed speakers and required outputs.
- [x] Invalid verdict attempts before deliberation are blocked.
- [x] The flow can stop safely at `adjourned_for_review`.

### V2-M3. Courtroom Dialogue Layer

Status:

- [x] Completed for V2 Phase 2

Generate natural but concise Vietnamese hearing dialogue:

- Clerk: formal opening, attendance, record keeping.
- Judge: procedure, questions, summaries, deliberation framing.
- Plaintiff: claims, evidence references, rebuttal.
- Defense: objections, counterarguments, evidence challenges.
- Evidence Agent: neutral evidence presentation.
- Verification Agents: fact-check and citation-check announcements.

Acceptance:

- [x] Transcript has real multi-turn courtroom dialogue, not only summaries.
- [x] Each party statement is grounded in evidence or explicitly marked ungrounded.
- [x] Dialogue remains concise enough for a demo report.
- [x] Role drift is detected and flagged.

### V2-M4. Evidence Examination And Debate

Status:

- [x] Completed for V2 Phase 2 baseline

Add a real examination layer:

- Judge introduces each evidence item.
- Plaintiff explains why it supports the claim.
- Defense accepts, disputes, or challenges it.
- Evidence Agent updates admissibility state.
- Debate rounds reference only admitted or review-pending evidence.

Acceptance:

- [x] Every important evidence item is examined at least once.
- [x] Disputed evidence cannot silently support a decision.
- [x] Debate turns include related `claim_id`, `evidence_id`, and `citation_id`.
- [x] Unresolved evidence moves to human review checklist.

### V2-M5. Deliberation And Decision Guard

Status:

- [x] Completed for V2 Phase 3

Create a guarded deliberation layer:

- Summarize established facts.
- Separate disputed and unproven facts.
- Map claims to evidence and citations.
- Decide whether the simulated outcome should be confident, limited, or explicitly risky.
- Block official judgment language.
- Allow demo-mode continuation even when human review is still recommended.

Allowed outcome types:

- `simulated_plaintiff_favored`
- `simulated_defense_favored`
- `simulated_partial_relief`
- `simulated_risky_requires_review`
- `adjourned_for_review`
- `requires_more_evidence`
- `no_simulated_decision`

Acceptance:

- [x] A simulated decision can be generated in demo mode even when human review is recommended.
- [x] If facts are unresolved, the output labels the decision as risky or limited and explains why.
- [x] The system never uses official wording like "the court orders".
- [x] Human review can be enabled later to approve, revise, or block the decision.

### V2-M6. Formal Trial Record Export

Status:

- [x] Completed for V2 Phase 4

Upgrade Markdown and HTML exports into a full trial-style record:

- Case header and participants.
- Opening formalities.
- Procedural timeline.
- Courtroom transcript.
- Evidence examination table.
- Debate and rebuttal summary.
- Verification findings.
- Deliberation summary.
- Simulated decision or no-decision result.
- Optional human review checklist and risk notes.
- Legal disclaimer.

Acceptance:

- [x] Report reads like formal court minutes.
- [x] Vietnamese labels are used in user-facing sections.
- [x] HTML preview uses formal, minimal legal styling.
- [x] Export remains readable without the frontend.

### V2-M7. Evaluation And Demo Fixtures

Status:

- [x] Backend completed for V2 Phase 5
- [x] Frontend handoff/rendering notes completed after the FE lane resumed

Add three stable V2 demo cases:

- Strong plaintiff case.
- Strong defense case.
- Ambiguous case requiring more evidence.

Acceptance:

- [x] Each fixture reaches the expected outcome type.
- [x] Smoke tests verify complete stage coverage.
- [x] Evaluation checks transcript completeness and grounding discipline.
- [x] Demo script can run one full V2 trial end-to-end.

## 4. Suggested Phase Plan

### Phase 0. Contracts And Fixtures

- [x] Add V2 shared schemas.
- [x] Add TypeScript type mirrors.
- [x] Add a complete V2 fixture.
- [x] Add migration notes from V1 to V2.

### Phase 1. Trial Procedure Runtime

- [x] Implement courtroom-facing stages.
- [x] Add speaker permission rules.
- [x] Add safe stop states.
- [x] Add smoke test for full stage traversal.

### Phase 2. Dialogue And Evidence Examination

- [x] Implement multi-turn courtroom dialogue.
- [x] Implement evidence examination rounds.
- [x] Add debate and rebuttal turns.
- [x] Add transcript compactness controls.

### Phase 3. Deliberation And Simulated Decision

- [x] Implement deliberation record.
- [x] Implement demo-mode decision guard.
- [x] Add simulated outcome generation.
- [x] Add risky-decision, no-decision, and adjournment paths.

### Phase 4. Formal Export

- [x] Upgrade Markdown report.
- [x] Upgrade HTML trial preview.
- [x] Add Vietnamese section labels.
- [x] Add report completeness checks.

### Phase 5. Evaluation And UI Handoff

- [x] Add V2 smoke and regression tests.
- [x] Add three stable demo cases.
- [x] Add API endpoints for frontend timeline/transcript rendering.
- [x] Write frontend handoff notes for trial transcript UI.
- [x] Add a config flag for `human_review_mode`: `optional`, `required`, or `off`.

## 5. Demo-Ready Definition

V2 is demo-ready when one command can produce a complete record with:

- Opening, appearance check, and procedure explanation.
- Plaintiff and defense statements.
- Evidence examination and challenge handling.
- Judge questions and party answers.
- Debate, rebuttal, and final statements.
- Deliberation summary.
- Simulated decision or explicit no-decision outcome.
- Optional human review status, checklist, and risk notes.
- Formal Markdown and HTML exports.
