# AI Courtroom Harness V2 Implementation Plan

V2 starts after the backend MVP and V1 procedural harness are stable. The goal is to make the output read and behave like a complete simulated civil hearing, while preserving the project boundary: this is an educational and decision-support simulation, not an official court judgment.

## 0. Progress Snapshot

- [ ] V2 Phase 0 trial-flow contracts are defined.
- [ ] V2 Phase 1 full trial procedure runtime is implemented.
- [ ] V2 Phase 2 courtroom dialogue layer is implemented.
- [ ] V2 Phase 3 deliberation and verdict guard is implemented.
- [ ] V2 Phase 4 formal trial record and simulated outcome export are implemented.
- [ ] V2 Phase 5 evaluation, demo fixtures, and UI hooks are implemented.

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

The system may produce a **simulated non-binding decision** only when evidence, citations, and human-review gates allow it. Otherwise, it must end with `requires_more_evidence`, `adjourned_for_review`, or `no_simulated_decision`.

## 2. Product Boundary

### In Scope

- Full civil-hearing narrative from opening to closing.
- Formal Vietnamese labels and transcript sections.
- Multi-turn judge, plaintiff, defense, clerk, evidence, fact-check, and citation-verifier dialogue.
- Courtroom procedure stages, not only backend harness stages.
- Evidence examination and party rebuttal rounds.
- Deliberation summary with strict grounding.
- Simulated outcome guarded by evidence and citation checks.
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

- [ ] Contracts support a complete hearing timeline.
- [ ] Existing V1 `HearingSession` remains backward compatible.
- [ ] Fixtures include one complete V2 trial transcript.

### V2-M2. Full Trial Procedure Runtime

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

- [ ] Runtime enforces stage order.
- [ ] Each stage has allowed speakers and required outputs.
- [ ] Invalid verdict attempts before deliberation are blocked.
- [ ] The flow can stop safely at `adjourned_for_review`.

### V2-M3. Courtroom Dialogue Layer

Generate natural but concise Vietnamese hearing dialogue:

- Clerk: formal opening, attendance, record keeping.
- Judge: procedure, questions, summaries, deliberation framing.
- Plaintiff: claims, evidence references, rebuttal.
- Defense: objections, counterarguments, evidence challenges.
- Evidence Agent: neutral evidence presentation.
- Verification Agents: fact-check and citation-check announcements.

Acceptance:

- [ ] Transcript has real multi-turn courtroom dialogue, not only summaries.
- [ ] Each party statement is grounded in evidence or explicitly marked ungrounded.
- [ ] Dialogue remains concise enough for a demo report.
- [ ] Role drift is detected and flagged.

### V2-M4. Evidence Examination And Debate

Add a real examination layer:

- Judge introduces each evidence item.
- Plaintiff explains why it supports the claim.
- Defense accepts, disputes, or challenges it.
- Evidence Agent updates admissibility state.
- Debate rounds reference only admitted or review-pending evidence.

Acceptance:

- [ ] Every important evidence item is examined at least once.
- [ ] Disputed evidence cannot silently support a decision.
- [ ] Debate turns include related `claim_id`, `evidence_id`, and `citation_id`.
- [ ] Unresolved evidence moves to human review checklist.

### V2-M5. Deliberation And Decision Guard

Create a guarded deliberation layer:

- Summarize established facts.
- Separate disputed and unproven facts.
- Map claims to evidence and citations.
- Decide whether a simulated outcome is allowed.
- Block official judgment language.

Allowed outcome types:

- `simulated_plaintiff_favored`
- `simulated_defense_favored`
- `simulated_partial_relief`
- `adjourned_for_review`
- `requires_more_evidence`
- `no_simulated_decision`

Acceptance:

- [ ] A simulated decision is generated only when guard checks pass.
- [ ] If facts are unresolved, the output says why no decision is reached.
- [ ] The system never uses official wording like "the court orders".
- [ ] Human review can approve, revise, or block the decision.

### V2-M6. Formal Trial Record Export

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
- Human review checklist.
- Legal disclaimer.

Acceptance:

- [ ] Report reads like formal court minutes.
- [ ] Vietnamese labels are used in user-facing sections.
- [ ] HTML preview uses formal, minimal legal styling.
- [ ] Export remains readable without the frontend.

### V2-M7. Evaluation And Demo Fixtures

Add three stable V2 demo cases:

- Strong plaintiff case.
- Strong defense case.
- Ambiguous case requiring more evidence.

Acceptance:

- [ ] Each fixture reaches the expected outcome type.
- [ ] Smoke tests verify complete stage coverage.
- [ ] Evaluation checks transcript completeness and grounding discipline.
- [ ] Demo script can run one full V2 trial end-to-end.

## 4. Suggested Phase Plan

### Phase 0. Contracts And Fixtures

- [ ] Add V2 shared schemas.
- [ ] Add TypeScript type mirrors.
- [ ] Add a complete V2 fixture.
- [ ] Add migration notes from V1 to V2.

### Phase 1. Trial Procedure Runtime

- [ ] Implement courtroom-facing stages.
- [ ] Add speaker permission rules.
- [ ] Add safe stop states.
- [ ] Add smoke test for full stage traversal.

### Phase 2. Dialogue And Evidence Examination

- [ ] Implement multi-turn courtroom dialogue.
- [ ] Implement evidence examination rounds.
- [ ] Add debate and rebuttal turns.
- [ ] Add transcript compactness controls.

### Phase 3. Deliberation And Simulated Decision

- [ ] Implement deliberation record.
- [ ] Implement decision guard.
- [ ] Add simulated outcome generation.
- [ ] Add no-decision and adjournment paths.

### Phase 4. Formal Export

- [ ] Upgrade Markdown report.
- [ ] Upgrade HTML trial preview.
- [ ] Add Vietnamese section labels.
- [ ] Add report completeness checks.

### Phase 5. Evaluation And UI Handoff

- [ ] Add V2 smoke and regression tests.
- [ ] Add three stable demo cases.
- [ ] Add API endpoints for frontend timeline/transcript rendering.
- [ ] Write frontend handoff notes for trial transcript UI.

## 5. Demo-Ready Definition

V2 is demo-ready when one command can produce a complete record with:

- Opening, appearance check, and procedure explanation.
- Plaintiff and defense statements.
- Evidence examination and challenge handling.
- Judge questions and party answers.
- Debate, rebuttal, and final statements.
- Deliberation summary.
- Simulated decision or explicit no-decision outcome.
- Human review status.
- Formal Markdown and HTML exports.

