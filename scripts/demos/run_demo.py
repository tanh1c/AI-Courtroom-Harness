from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
import warnings
import webbrowser
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
from packages.orchestration.python.ai_court_orchestration.service import (
    get_courtroom_simulation_service,
)
from packages.reporting.python.ai_court_reporting.service import (
    get_html_report_service,
)

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
<< /Length 129 >>
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
0000000249 00000 n 
0000000429 00000 n 
trailer
<< /Root 1 0 R /Size 6 >>
startxref
499
%%EOF
"""


def write_sample_pdf(path: Path) -> None:
    path.write_bytes(MINIMAL_PDF_BYTES)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full AI Courtroom Harness demo flow and export markdown + HTML preview."
    )
    parser.add_argument(
        "--open-preview",
        action="store_true",
        help="Open the generated HTML preview in the default browser.",
    )
    parser.add_argument(
        "--reviewer-name",
        default="Codex Demo Reviewer",
        help="Human reviewer name used for the review approval step.",
    )
    return parser.parse_args()


def save_html_preview(markdown_path: Path, markdown_text: str, case_id: str) -> Path:
    html_path = markdown_path.with_name("report_preview.html")
    html = get_html_report_service().render(
        title=f"AI Courtroom Harness Report - {case_id}",
        markdown_text=markdown_text,
    )
    html_path.write_text(html, encoding="utf-8")
    return html_path


def main() -> None:
    args = parse_args()
    logging.getLogger("pypdf").setLevel(logging.ERROR)

    temp_dir = Path(tempfile.mkdtemp(prefix="ai_court_demo_"))
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

    review_response = client.post(
        f"/api/v1/cases/{case_id}/review",
        json={
            "reviewer_name": args.reviewer_name,
            "decision": "approve",
            "notes": "Demo flow approved for scripted export and HTML preview.",
            "checklist_updates": [
                "Reviewer approved the current demo report for scripted presentation use."
            ],
        },
    )
    review_response.raise_for_status()
    review = review_response.json()

    export_response = client.post(f"/api/v1/reports/{case_id}/markdown")
    export_response.raise_for_status()
    exported = export_response.json()

    markdown_path = Path(exported["markdown_path"])
    html_path = save_html_preview(markdown_path, exported["markdown"], case_id)
    llm_provider = get_courtroom_simulation_service().llm_service.provider_label()

    summary = {
        "case_id": case_id,
        "provider_used": llm_provider,
        "pre_review_status": simulation["case"]["status"],
        "post_review_status": review["report_status"],
        "human_review_blocked": review["human_review"]["blocked"],
        "report_markdown_path": str(markdown_path),
        "report_html_preview_path": str(html_path),
        "judge_disputed_points": simulation["judge_summary"]["main_disputed_points"],
        "citations_used": [citation["citation_id"] for citation in simulation["case"]["citations"]],
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.open_preview:
        webbrowser.open(html_path.resolve().as_uri())


if __name__ == "__main__":
    main()
