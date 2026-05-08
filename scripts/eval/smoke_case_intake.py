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
(Hop dong mua ban laptop. Gia tri 25.000.000 dong. Thanh toan truoc 15.000.000 dong. Giao hang ngay 15/04/2026.) Tj
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
    temp_dir = Path(tempfile.mkdtemp(prefix="ai_court_smoke_"))
    pdf_path = temp_dir / "hop_dong_laptop.pdf"
    write_sample_pdf(pdf_path)

    client = TestClient(app)

    create_response = client.post(
        "/api/v1/cases",
        json={
            "title": "Tranh chấp hợp đồng mua bán laptop",
            "case_type": "civil_contract_dispute",
            "language": "vi",
            "narrative": (
                "Ngày 10/04/2026, bà C đặt mua của cửa hàng D một laptop trị giá 25.000.000 đồng. "
                "Bà C đã chuyển khoản trước 15.000.000 đồng. Hai bên hẹn giao hàng ngày 15/04/2026 "
                "nhưng cửa hàng D chưa giao hàng và yêu cầu thanh toán đủ toàn bộ trước khi giao. "
                "Bà C yêu cầu hoàn tiền và bồi thường chi phí phát sinh."
            ),
            "attachments": [],
        },
    )
    create_response.raise_for_status()
    created_case = create_response.json()["case"]
    case_id = created_case["case_id"]

    with pdf_path.open("rb") as handle:
        upload_response = client.post(
            f"/api/v1/cases/{case_id}/attachments",
            data={"note": "Hợp đồng mua bán laptop"},
            files={"file": ("hop_dong_laptop.pdf", handle, "application/pdf")},
        )
    upload_response.raise_for_status()

    parse_response = client.post(f"/api/v1/cases/{case_id}/parse")
    parse_response.raise_for_status()
    parsed_case = parse_response.json()["case"]

    detail_response = client.get(f"/api/v1/cases/{case_id}")
    detail_response.raise_for_status()
    detail_case = detail_response.json()

    state_response = client.get(f"/api/v1/cases/{case_id}/state")
    state_response.raise_for_status()
    state_case = state_response.json()["case"]

    list_response = client.get("/api/v1/cases")
    list_response.raise_for_status()
    listed_cases = list_response.json()["cases"]

    print("created_case_id:", case_id)
    print("listed_case_count:", len(listed_cases))
    print("detail_status:", detail_case["record"]["status"])
    print("state_status:", state_case["status"])
    print("fact_count:", len(parsed_case["facts"]))
    print("evidence_count:", len(parsed_case["evidence"]))
    print("attachment_parse_statuses:", [item["extraction_status"] for item in parsed_case["attachment_parses"]])
    print("attachment_excerpt_present:", [bool(item["extracted_text_excerpt"]) for item in parsed_case["attachment_parses"]])
    print("issue_titles:", [issue["title"] for issue in parsed_case["legal_issues"]])


if __name__ == "__main__":
    main()
