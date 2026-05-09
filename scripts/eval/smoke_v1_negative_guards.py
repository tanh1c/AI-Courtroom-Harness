from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.orchestration.python.ai_court_orchestration.v1_service import (
    HearingRuntimeError,
    get_courtroom_v1_runtime_service,
)
from packages.shared.python.ai_court_shared.schemas import (
    AgentName,
    CaseState,
    Claim,
    ClaimConfidence,
    HearingStage,
)

PARSE_FIXTURE = ROOT_DIR / "packages" / "shared" / "fixtures" / "sample_case_01.parse.json"


def load_case_state() -> CaseState:
    return CaseState.model_validate(json.loads(PARSE_FIXTURE.read_text(encoding="utf-8")))


def main() -> None:
    service = get_courtroom_v1_runtime_service()
    session = service.start(load_case_state())

    invalid_stage_blocked = False
    try:
        service.advance(session, expected_stage=HearingStage.LEGAL_RETRIEVAL)
    except HearingRuntimeError:
        invalid_stage_blocked = True
    assert invalid_stage_blocked, "Expected invalid stage transition to be blocked."

    session.current_stage = HearingStage.PARTY_RESPONSES
    session.case.citations = []
    session.case.claims = [
        Claim(
            claim_id="CLAIM_NEG_001",
            speaker=AgentName.PLAINTIFF_AGENT,
            content="Unsupported test claim without evidence or citations.",
            evidence_ids=[],
            citation_ids=[],
            confidence=ClaimConfidence.LOW,
        ),
        Claim(
            claim_id="CLAIM_NEG_002",
            speaker=AgentName.DEFENSE_AGENT,
            content="Invalid citation test claim.",
            evidence_ids=["EVID_001"],
            citation_ids=["LAW_FAKE_999"],
            confidence=ClaimConfidence.LOW,
        ),
    ]

    checked = service.advance(session, expected_stage=HearingStage.FACT_CHECK)
    assert checked.fact_check is not None
    assert "CLAIM_NEG_001" in checked.fact_check.unsupported_claims
    assert "CLAIM_NEG_002" in checked.fact_check.citation_mismatches

    print(
        json.dumps(
            {
                "invalid_stage_blocked": invalid_stage_blocked,
                "unsupported_claims": checked.fact_check.unsupported_claims,
                "citation_mismatches": checked.fact_check.citation_mismatches,
                "risk_level": checked.fact_check.risk_level.value,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
