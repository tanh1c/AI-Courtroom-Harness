from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.api.app.main import create_case, parse_case
from packages.shared.python.ai_court_shared.schemas import CaseAttachment, CaseCreateRequest, CaseType


def main() -> None:
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

    print("created_case_id:", created.case.case_id)
    print("status:", parsed.case.status)
    print("fact_count:", len(parsed.case.facts))
    print("evidence_count:", len(parsed.case.evidence))
    print("issue_titles:", [issue.title for issue in parsed.case.legal_issues])


if __name__ == "__main__":
    main()
