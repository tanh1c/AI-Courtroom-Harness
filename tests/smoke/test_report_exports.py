from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_review_ready_case_exports_markdown_and_printable_reports() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/cases",
        json={
            "title": "Printable export smoke case",
            "case_type": "civil_contract_dispute",
            "language": "vi",
            "narrative": (
                "Ngày 24/01/2026, các bên ký hợp đồng mua bán xe. "
                "Bên mua đã thanh toán 28.000.000 đồng nhưng bên bán chưa giao xe đúng hạn. "
                "Nguyên đơn yêu cầu hoàn trả tiền và bồi thường chi phí phát sinh."
            ),
            "attachments": [],
        },
    )
    assert create_response.status_code == 200
    case_id = create_response.json()["case"]["case_id"]

    assert client.post(f"/api/v1/cases/{case_id}/parse").status_code == 200
    simulate_response = client.post(f"/api/v1/cases/{case_id}/simulate")
    assert simulate_response.status_code == 200

    blocked_export = client.post(f"/api/v1/reports/{case_id}/printable")
    assert blocked_export.status_code == 409

    review_response = client.post(
        f"/api/v1/cases/{case_id}/review",
        json={
            "reviewer_name": "Smoke Reviewer",
            "decision": "approve",
            "notes": "Approved for export smoke test.",
            "checklist_updates": ["Confirmed non-binding report export."],
        },
    )
    assert review_response.status_code == 200
    assert review_response.json()["report_status"] == "report_ready"

    markdown_response = client.post(f"/api/v1/reports/{case_id}/markdown")
    assert markdown_response.status_code == 200
    markdown_payload = markdown_response.json()
    assert markdown_payload["markdown_path"].endswith("report.md")
    assert "AI Courtroom Harness Report" in markdown_payload["markdown"]

    printable_response = client.post(f"/api/v1/reports/{case_id}/printable")
    assert printable_response.status_code == 200
    printable_payload = printable_response.json()
    assert printable_payload["printable_path"].endswith("report_printable.html")
    assert "<!DOCTYPE html>" in printable_payload["html"]
    assert "Formal Report Preview" in printable_payload["html"]

    get_printable_response = client.get(f"/api/v1/reports/{case_id}/printable")
    assert get_printable_response.status_code == 200
    assert get_printable_response.json()["printable_path"] == printable_payload["printable_path"]
