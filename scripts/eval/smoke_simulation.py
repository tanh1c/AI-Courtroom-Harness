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
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
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
    temp_dir = Path(tempfile.mkdtemp(prefix="ai_court_phase3_"))
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

    simulate_response = client.post(f"/api/v1/cases/{case_id}/simulate")
    simulate_response.raise_for_status()
    simulation = simulate_response.json()

    audit_response = client.get(f"/api/v1/cases/{case_id}/audit")
    audit_response.raise_for_status()
    audit = audit_response.json()

    report_response = client.get(f"/api/v1/reports/{case_id}")
    report_response.raise_for_status()
    report = report_response.json()

    print("case_id:", case_id)
    print("case_status:", simulation["case"]["status"])
    print("claim_count:", len(simulation["case"]["claims"]))
    print("turn_agents:", [turn["agent"] for turn in simulation["case"]["agent_turns"]])
    print("citation_count:", len(simulation["case"]["citations"]))
    print("risk_level:", simulation["fact_check"]["risk_level"])
    print("audit_event_count:", len(audit["audit_trail"]))
    print("human_review_required:", audit["human_review"]["required"])
    print("human_review_blocked:", audit["human_review"]["blocked"])
    print("report_status:", report["report_status"])
    print("report_turn_count:", len(report["generated_from_turns"]))
    print("disputed_points:", simulation["judge_summary"]["main_disputed_points"])


if __name__ == "__main__":
    main()
