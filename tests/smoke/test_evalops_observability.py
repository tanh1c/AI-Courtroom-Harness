from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_simulated_case_creates_eval_run_with_trace_and_metrics() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/cases",
        json={
            "title": "EvalOps smoke case",
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
    assert client.post(f"/api/v1/cases/{case_id}/simulate").status_code == 200

    eval_response = client.post(f"/api/v1/cases/{case_id}/eval-runs")
    assert eval_response.status_code == 200
    eval_run = eval_response.json()
    assert eval_run["case_id"] == case_id
    assert eval_run["eval_run_id"].startswith("EVAL_")
    assert eval_run["status"] in {"ok", "needs_review"}
    assert eval_run["metrics"]
    assert {metric["name"] for metric in eval_run["metrics"]} >= {
        "unsupported_claims",
        "citation_mismatches",
        "rejected_citations",
        "human_review_blocked",
    }
    assert eval_run["trace_steps"]
    assert eval_run["human_review"]["blocked"] is True

    list_response = client.get(f"/api/v1/cases/{case_id}/eval-runs")
    assert list_response.status_code == 200
    eval_runs = list_response.json()["eval_runs"]
    assert eval_runs[0]["eval_run_id"] == eval_run["eval_run_id"]
