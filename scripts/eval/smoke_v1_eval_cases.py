from __future__ import annotations

import json
import logging
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

warnings.filterwarnings(
    "ignore",
    message=r"The default value of `allowed_objects` will change.*",
)

from apps.api.app.main import app

FIXTURE_PATH = ROOT_DIR / "packages" / "shared" / "fixtures" / "v1_demo_cases.json"


def minimal_pdf_bytes(text: str) -> bytes:
    safe_text = "".join(character if ord(character) < 128 else " " for character in text)
    stream = f"""BT
/F1 12 Tf
72 720 Td
({safe_text[:180]}) Tj
ET"""
    stream_bytes = stream.encode("ascii", errors="ignore")
    return b"""%PDF-1.4
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
<< /Length """ + str(len(stream_bytes)).encode("ascii") + b""" >>
stream
""" + stream_bytes + b"""
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


def load_demo_cases() -> list[dict[str, Any]]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def run_case(client: TestClient, demo: dict[str, Any], temp_dir: Path) -> dict[str, Any]:
    create_response = client.post(
        "/api/v1/cases",
        json={
            "title": demo["title"],
            "case_type": demo["case_type"],
            "language": demo["language"],
            "narrative": demo["narrative"],
            "attachments": [],
        },
    )
    create_response.raise_for_status()
    case_id = create_response.json()["case"]["case_id"]

    pdf_path = temp_dir / f"{demo['demo_id']}.pdf"
    pdf_path.write_bytes(minimal_pdf_bytes(demo["attachment_text"]))
    with pdf_path.open("rb") as handle:
        upload_response = client.post(
            f"/api/v1/cases/{case_id}/attachments",
            data={"note": demo["attachment_note"]},
            files={"file": (pdf_path.name, handle, "application/pdf")},
        )
    upload_response.raise_for_status()

    client.post(f"/api/v1/cases/{case_id}/parse").raise_for_status()
    start_response = client.post(f"/api/v1/cases/{case_id}/hearing/start")
    start_response.raise_for_status()
    session = start_response.json()

    while session["current_stage"] != "closing_record":
        next_stage = session["stage_order"][session["stage_order"].index(session["current_stage"]) + 1]
        advance_response = client.post(
            f"/api/v1/cases/{case_id}/hearing/advance",
            json={"expected_stage": next_stage},
        )
        advance_response.raise_for_status()
        session = advance_response.json()

    outcome_response = client.get(f"/api/v1/cases/{case_id}/outcome")
    outcome_response.raise_for_status()
    outcome = outcome_response.json()["outcome_candidates"][0]

    markdown_response = client.post(f"/api/v1/cases/{case_id}/hearing/record/markdown")
    markdown_response.raise_for_status()
    markdown_record = markdown_response.json()
    html_response = client.post(f"/api/v1/cases/{case_id}/hearing/record/html")
    html_response.raise_for_status()
    html_record = html_response.json()

    expected = demo["expected"]
    assert len(session["stage_order"]) >= expected["min_stage_count"]
    assert len(session["evidence_challenges"]) >= expected["min_challenge_count"]
    assert len(session["clarification_questions"]) >= expected["min_question_count"]
    assert outcome["disposition"] == expected["expected_outcome_disposition"]
    assert outcome["requires_human_review"] is True
    assert session["human_review"]["blocked"] is True
    assert "V1 Simulated Hearing Record" in markdown_record["markdown"]
    assert html_record["html_path"].endswith("hearing_v1_record.html")

    return {
        "demo_id": demo["demo_id"],
        "case_id": case_id,
        "stage_count": len(session["stage_order"]),
        "turn_count": len(session["turns"]),
        "challenge_count": len(session["evidence_challenges"]),
        "question_count": len(session["clarification_questions"]),
        "outcome": outcome["disposition"],
        "markdown_path": markdown_record["markdown_path"],
        "html_path": html_record["html_path"],
    }


def main() -> None:
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    client = TestClient(app)
    temp_dir = Path(tempfile.mkdtemp(prefix="ai_court_v1_eval_"))
    results = [run_case(client, demo, temp_dir) for demo in load_demo_cases()]
    print(json.dumps({"v1_demo_case_count": len(results), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
