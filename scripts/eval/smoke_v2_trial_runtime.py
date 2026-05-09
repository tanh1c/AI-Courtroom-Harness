from __future__ import annotations

import logging
import sys
import tempfile
import warnings
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

warnings.filterwarnings(
    "ignore",
    message=r"The default value of `allowed_objects` will change.*",
)

from apps.api.app.main import app
from packages.orchestration.python.ai_court_orchestration.v2_service import (
    TrialRuntimeError,
    get_courtroom_v2_runtime_service,
)
from packages.shared.python.ai_court_shared.schemas import (
    AgentName,
    CaseState,
    HumanReviewMode,
    TrialProcedureStage,
)

MINIMAL_PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 1 /Kids [3 0 R] >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >>
endobj
4 0 obj
<< /Length 119 >>
stream
BT
/F1 12 Tf
72 720 Td
(Hop dong mua ban xe may. Gia tri 40.000.000 dong. Thanh toan 70 phan tram khi ky. Giao xe ngay 12/03/2026.) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000063 00000 n 
0000000122 00000 n 
0000000248 00000 n 
0000000418 00000 n 
trailer
<< /Root 1 0 R /Size 6 >>
startxref
488
%%EOF
"""


def write_sample_pdf(path: Path) -> None:
    path.write_bytes(MINIMAL_PDF_BYTES)


def main() -> None:
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    temp_dir = Path(tempfile.mkdtemp(prefix="ai_court_v2_"))
    pdf_path = temp_dir / "hop_dong_xe_may.pdf"
    write_sample_pdf(pdf_path)

    client = TestClient(app)
    create_response = client.post(
        "/api/v1/cases",
        json={
            "title": "Tranh chấp hợp đồng mua bán xe máy",
            "case_type": "civil_contract_dispute",
            "language": "vi",
            "narrative": (
                "Ngày 05/03/2026, ông B ký hợp đồng mua của ông A một xe máy trị giá 40.000.000 đồng. "
                "Ông B đã chuyển khoản trước 28.000.000 đồng. Hạn giao xe là ngày 12/03/2026 "
                "nhưng ông A chưa giao xe và yêu cầu thanh toán đủ 100% trước khi giao. "
                "Ông B yêu cầu giao xe hoặc hoàn trả tiền đã nhận và bồi thường chi phí phát sinh."
            ),
            "attachments": [],
        },
    )
    create_response.raise_for_status()
    case_id = create_response.json()["case"]["case_id"]

    with pdf_path.open("rb") as handle:
        upload_response = client.post(
            f"/api/v1/cases/{case_id}/attachments",
            data={"note": "Hợp đồng mua bán xe máy"},
            files={"file": ("hop_dong_xe_may.pdf", handle, "application/pdf")},
        )
    upload_response.raise_for_status()

    parse_response = client.post(f"/api/v1/cases/{case_id}/parse")
    parse_response.raise_for_status()

    start_response = client.post(
        f"/api/v1/cases/{case_id}/trial-v2/start",
        params={"human_review_mode": "optional"},
    )
    start_response.raise_for_status()
    session = start_response.json()

    invalid_advance_response = client.post(
        f"/api/v1/cases/{case_id}/trial-v2/advance",
        json={"expected_stage": "plaintiff_claim_statement"},
    )
    assert invalid_advance_response.status_code == 409, invalid_advance_response.text

    service = get_courtroom_v2_runtime_service()
    try:
        service.assert_speaker_allowed(
            TrialProcedureStage.SIMULATED_DECISION,
            AgentName.PLAINTIFF_AGENT,
        )
    except TrialRuntimeError:
        invalid_speaker_guard = True
    else:
        invalid_speaker_guard = False
    assert invalid_speaker_guard, "Expected invalid speaker guard to reject plaintiff verdict turn."

    fixture_case = CaseState.model_validate_json(
        (ROOT_DIR / "packages/shared/fixtures/sample_case_01.parse.json").read_text(encoding="utf-8")
    )
    required_review_session = service.run_all(
        fixture_case,
        human_review_mode=HumanReviewMode.REQUIRED,
    )
    assert required_review_session.simulated_decision is not None
    assert required_review_session.simulated_decision.disposition.value == "adjourned_for_review"
    assert required_review_session.human_review.blocked is True

    while session["current_stage"] != "closing_record":
        next_stage = session["stage_order"][session["stage_order"].index(session["current_stage"]) + 1]
        advance_response = client.post(
            f"/api/v1/cases/{case_id}/trial-v2/advance",
            json={"expected_stage": next_stage},
        )
        advance_response.raise_for_status()
        session = advance_response.json()

    persisted_response = client.get(f"/api/v1/cases/{case_id}/trial-v2")
    persisted_response.raise_for_status()
    persisted = persisted_response.json()

    stage_turns = {stage: 0 for stage in persisted["stage_order"]}
    for turn in persisted["dialogue_turns"]:
        stage_turns[turn["trial_stage"]] += 1

    assert persisted["current_stage"] == "closing_record"
    assert persisted["status"] == "report_ready"
    assert len(persisted["stage_order"]) == 14
    assert all(count > 0 for count in stage_turns.values()), stage_turns
    assert len(persisted["appearances"]) == 4
    assert len(persisted["procedural_acts"]) >= 3
    assert len(persisted["evidence_examinations"]) >= 1
    assert persisted["debate_rounds"], "Expected debate round."
    assert len(persisted["final_statements"]) == 2
    assert persisted["deliberation"] is not None
    assert persisted["decision_guard"] is not None
    assert persisted["decision_guard"]["allowed_to_emit"] is True
    assert persisted["simulated_decision"] is not None
    assert persisted["simulated_decision"]["non_binding_disclaimer"]
    assert persisted["human_review"]["blocked"] is False

    print("case_id:", case_id)
    print("session_id:", persisted["session_id"])
    print("current_stage:", persisted["current_stage"])
    print("stage_count:", len(persisted["stage_order"]))
    print("dialogue_turn_count:", len(persisted["dialogue_turns"]))
    print("invalid_stage_guard:", invalid_advance_response.status_code)
    print("invalid_speaker_guard:", invalid_speaker_guard)
    print("required_mode_safe_stop:", required_review_session.simulated_decision.disposition.value)
    print("appearance_count:", len(persisted["appearances"]))
    print("procedural_act_count:", len(persisted["procedural_acts"]))
    print("evidence_examination_count:", len(persisted["evidence_examinations"]))
    print("debate_round_count:", len(persisted["debate_rounds"]))
    print("final_statement_count:", len(persisted["final_statements"]))
    print("decision_disposition:", persisted["simulated_decision"]["disposition"])
    print("decision_risk:", persisted["simulated_decision"]["risk_level"])
    print("human_review_mode:", persisted["human_review_mode"])
    print("human_review_blocked:", persisted["human_review"]["blocked"])


if __name__ == "__main__":
    main()
