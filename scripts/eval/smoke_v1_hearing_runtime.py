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
    temp_dir = Path(tempfile.mkdtemp(prefix="ai_court_v1_"))
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

    start_response = client.post(f"/api/v1/cases/{case_id}/hearing/start")
    start_response.raise_for_status()
    session = start_response.json()

    invalid_advance_response = client.post(
        f"/api/v1/cases/{case_id}/hearing/advance",
        json={"expected_stage": "legal_retrieval"},
    )
    assert invalid_advance_response.status_code == 409, invalid_advance_response.text

    while session["current_stage"] != "closing_record":
        next_stage = session["stage_order"][session["stage_order"].index(session["current_stage"]) + 1]
        advance_response = client.post(
            f"/api/v1/cases/{case_id}/hearing/advance",
            json={"expected_stage": next_stage},
        )
        advance_response.raise_for_status()
        session = advance_response.json()

    persisted_response = client.get(f"/api/v1/cases/{case_id}/hearing")
    persisted_response.raise_for_status()
    persisted = persisted_response.json()

    challenges_response = client.get(f"/api/v1/cases/{case_id}/evidence/challenges")
    challenges_response.raise_for_status()
    challenges = challenges_response.json()

    verification_response = client.get(f"/api/v1/cases/{case_id}/verification")
    verification_response.raise_for_status()
    verification = verification_response.json()

    outcome_response = client.get(f"/api/v1/cases/{case_id}/outcome")
    outcome_response.raise_for_status()
    outcome_payload = outcome_response.json()

    markdown_response = client.post(f"/api/v1/cases/{case_id}/hearing/record/markdown")
    markdown_response.raise_for_status()
    markdown_record = markdown_response.json()

    html_response = client.post(f"/api/v1/cases/{case_id}/hearing/record/html")
    html_response.raise_for_status()
    html_record = html_response.json()

    agents_by_stage = {
        turn["hearing_stage"]: turn["agent"]
        for turn in persisted["turns"]
    }
    assert agents_by_stage["evidence_presentation"] == "evidence_agent"
    assert agents_by_stage["evidence_challenge"] == "evidence_agent"
    assert agents_by_stage["fact_check"] == "fact_check_agent"
    assert agents_by_stage["citation_verification"] == "citation_verifier_agent"
    assert challenges["challenges"], "Expected at least one evidence challenge."
    assert challenges["evidence_agent_turns"], "Expected evidence agent turns in challenge endpoint."
    assert verification["fact_check"] is not None, "Expected fact-check result."
    assert verification["citation_verification"] is not None, "Expected citation verification result."
    assert len(verification["verification_turns"]) == 2, "Expected fact-check and citation verifier turns."
    assert verification["tool_calls"], "Expected verification tool call trace."
    assert len(persisted["clarification_questions"]) >= 2, "Expected at least two clarification questions."
    expected_response_count = len(persisted["clarification_questions"]) * 2
    assert len(persisted["party_responses"]) == expected_response_count, "Expected plaintiff and defense responses for each question."
    for response in persisted["party_responses"]:
        content = response["content"].lower()
        grounded = response["evidence_ids"] or response["citation_ids"] or "chưa có chứng cứ" in content or "chưa có citation" in content
        assert grounded, f"Party response lacks evidence/citation discipline: {response['response_id']}"
    unresolved_questions = [
        question for question in persisted["clarification_questions"] if question["status"] != "ok"
    ]
    assert unresolved_questions, "Expected unresolved clarification questions for human review."
    checklist_text = "\n".join(persisted["human_review"]["checklist"])
    for question in unresolved_questions:
        assert question["question_id"] in checklist_text, f"Missing unresolved question in checklist: {question['question_id']}"
    assert outcome_payload["outcome_candidates"], "Expected non-binding outcome candidate."
    assert outcome_payload["preliminary_assessment_turns"], "Expected preliminary assessment turn."
    outcome = outcome_payload["outcome_candidates"][0]
    assert outcome["requires_human_review"] is True, "Outcome candidate must require human review."
    assert outcome["disposition"] == "requires_more_evidence", "Risky sample should require more evidence."
    assert outcome["supported_claim_ids"], "Outcome should reference grounded claim IDs."
    assert outcome["evidence_ids"], "Outcome should reference evidence IDs."
    assert outcome["citation_ids"], "Outcome should reference accepted citation IDs."
    outcome_text = f"{outcome['disposition']} {outcome['rationale']} {outcome['disclaimer']}".lower()
    official_markers = [
        "tòa tuyên",
        "tòa án tuyên",
        "tòa quyết định",
        "buộc bị đơn",
        "buộc nguyên đơn",
        "court hereby decides",
        "court orders",
    ]
    assert not any(marker in outcome_text for marker in official_markers), "Outcome used official judgment language."
    assert outcome_payload["human_review"]["blocked"] is True, "Outcome must stay behind human review."
    assert outcome["outcome_id"] in checklist_text, "Outcome review item missing from human review checklist."
    markdown_text = markdown_record["markdown"]
    assert "V1 Simulated Hearing Record" in markdown_text
    assert "Evidence Challenges" in markdown_text
    assert "Judge Clarification Questions And Responses" in markdown_text
    assert "Non-Binding Proposed Outcome" in markdown_text
    assert outcome["outcome_id"] in markdown_text
    assert html_record["html_path"].endswith("hearing_v1_record.html")
    assert "<html" in html_record["html"].lower()

    print("case_id:", case_id)
    print("session_id:", persisted["session_id"])
    print("current_stage:", persisted["current_stage"])
    print("stage_count:", len(persisted["stage_order"]))
    print("turn_count:", len(persisted["turns"]))
    print("invalid_stage_guard:", invalid_advance_response.status_code)
    print("claim_count:", len(persisted["case"]["claims"]))
    print("citation_count:", len(persisted["case"]["citations"]))
    print("challenge_count:", len(persisted["evidence_challenges"]))
    print("question_count:", len(persisted["clarification_questions"]))
    print("response_count:", len(persisted["party_responses"]))
    print("unresolved_question_count:", len(unresolved_questions))
    print("verification_turn_count:", len(verification["verification_turns"]))
    print("verification_tool_call_count:", len(verification["tool_calls"]))
    print("outcome_count:", len(outcome_payload["outcome_candidates"]))
    print("outcome_disposition:", outcome["disposition"])
    print("hearing_record_markdown_path:", markdown_record["markdown_path"])
    print("hearing_record_html_path:", html_record["html_path"])
    print("human_review_blocked:", persisted["human_review"]["blocked"])


if __name__ == "__main__":
    main()
