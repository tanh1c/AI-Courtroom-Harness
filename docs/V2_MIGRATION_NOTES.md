# V2 Migration Notes

V2 adds a courtroom-facing trial simulation layer on top of the existing MVP and V1 harness contracts. It does not replace `HearingSession` or the V1 procedural runtime.

## Contract Strategy

- Keep V1 `HearingSession` stable for current backend smoke tests and API consumers.
- Add `V2TrialSession` for full trial-style simulations.
- Use `TrialProcedureStage` for courtroom procedure stages instead of reusing V1 `HearingStage`.
- Keep `CaseState`, `Claim`, `Evidence`, `Citation`, `FactCheckResult`, and `CitationVerificationResult` shared across MVP, V1, and V2.

## Human Review Mode

V2 supports `human_review_mode`:

- `optional`: demo mode. The flow may reach a simulated decision while surfacing risk notes and reviewer checklist items.
- `required`: stricter mode for decision-support demos where reviewer approval should block final export.
- `off`: local smoke/testing mode where review metadata is omitted or non-blocking.

The default V2 fixture uses `optional` because the current product goal is to show a complete simulated hearing from opening to closing.

## Decision Language

V2 may emit a `SimulatedDecision`, but it must remain non-binding. Do not use official judgment wording such as "the court orders" or "the court hereby decides". If evidence is weak, use `simulated_risky_requires_review`, `requires_more_evidence`, or `no_simulated_decision`.

## Frontend Impact

Frontend work should render V2 as a trial timeline:

- appearances
- procedural acts
- dialogue transcript
- evidence examinations
- debate rounds
- final statements
- deliberation
- simulated decision and risk notes

The V1 hearing record UI can stay available for technical harness inspection.

