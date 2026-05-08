from __future__ import annotations

import sys
import tempfile
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.api.app.main import create_case, get_case_detail, get_case_state, parse_case
from packages.shared.python.ai_court_shared.schemas import CaseAttachment, CaseCreateRequest, CaseType


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

    request = CaseCreateRequest(
        title="Tranh chấp hợp đồng mua bán laptop",
        case_type=CaseType.CIVIL_CONTRACT_DISPUTE,
        narrative=(
            "Ngày 10/04/2026, bà C đặt mua của cửa hàng D một laptop trị giá 25.000.000 đồng. "
            "Bà C đã chuyển khoản trước 15.000.000 đồng. Hai bên hẹn giao hàng ngày 15/04/2026 "
            "nhưng cửa hàng D chưa giao hàng và yêu cầu thanh toán đủ toàn bộ trước khi giao. "
            "Bà C yêu cầu hoàn tiền và bồi thường chi phí phát sinh."
        ),
        attachments=[
            CaseAttachment(
                attachment_id="ATT_LOCAL_001",
                filename="hop_dong_laptop.pdf",
                media_type="application/pdf",
                note="Hợp đồng mua bán laptop",
                local_path=str(pdf_path),
            ),
            CaseAttachment(
                attachment_id="ATT_LOCAL_002",
                filename="bien_lai_chuyen_khoan.png",
                media_type="image/png",
                note="Biên lai chuyển khoản 15.000.000 đồng",
            ),
        ],
    )
    created = create_case(request)
    parsed = parse_case(created.case.case_id)
    detail = get_case_detail(created.case.case_id)
    state = get_case_state(created.case.case_id)

    print("created_case_id:", created.case.case_id)
    print("status:", parsed.case.status)
    print("fact_count:", len(parsed.case.facts))
    print("evidence_count:", len(parsed.case.evidence))
    print("issue_titles:", [issue.title for issue in parsed.case.legal_issues])
    print("detail_status:", detail.record.status)
    print("state_status:", state.case.status)
    print(
        "attachment_parse_statuses:",
        [attachment.extraction_status for attachment in parsed.case.attachment_parses],
    )
    print(
        "attachment_excerpt_present:",
        [bool(attachment.extracted_text_excerpt) for attachment in parsed.case.attachment_parses],
    )


if __name__ == "__main__":
    main()
