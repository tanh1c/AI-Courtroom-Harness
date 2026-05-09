# V1 Migration Notes

These notes explain how the V1 contracts extend the MVP contracts without breaking the current MVP flow.

## Contract Strategy

MVP contracts remain valid.

V1 adds new models around the existing case state instead of replacing it:

- `CaseState` remains the core parsed case object.
- `AgentTurn` remains the MVP turn shape.
- `V1AgentTurn` extends `AgentTurn` with `hearing_stage` and `tool_call_ids`.
- `HearingSession` wraps a full stage-based simulated hearing.

This keeps existing endpoints and fixtures usable while V1 runtime work is developed.

## New V1 Fixture

Canonical V1 fixture:

- `packages/shared/fixtures/sample_case_01.v1_hearing_session.json`

Use this fixture first when building:

- stage-based runtime
- V1 report renderer
- V1 frontend panels
- negative tests for role and citation violations

## Important New Concepts

- `HearingStage`: procedural stage for each hearing turn.
- `RolePermission`: policy for which agent may act in each stage.
- `EvidenceChallenge`: challenge record for disputed evidence.
- `ClarificationQuestion`: judge question attached to claims, evidence, and citations.
- `PartyResponse`: response from plaintiff or defense.
- `OutcomeCandidate`: non-binding proposed outcome with explicit disclaimer.
- `HarnessViolation`: structured record for role, grounding, or policy violations.

## Compatibility Rules

- Do not add required V1-only fields to MVP response models yet.
- Do not make `hearing_stage` required on the existing `AgentTurn`.
- Use `V1AgentTurn` only inside `HearingSession`.
- Keep V1 proposed outcomes non-binding and blocked by human review.
- Continue filtering rejected or expired citations out of final legal-basis sections.

## Recommended Runtime Migration Path

1. Load the existing `CaseState`.
2. Create a `HearingSession` around that case.
3. Append `V1AgentTurn` records stage by stage.
4. Run role permission checks before each turn.
5. Store evidence challenges and clarification responses inside the session.
6. Generate outcome candidates only after verification.
7. Require human review before exporting V1 report output.

## Frontend Migration Path

The MVP frontend can keep using current endpoints.

V1 frontend work should initially use the fixture shape and display:

- hearing stages
- V1 turns
- evidence challenges
- clarification questions
- party responses
- harness violations
- non-binding outcome candidates

Backend endpoints can be connected after the V1 runtime exists.
