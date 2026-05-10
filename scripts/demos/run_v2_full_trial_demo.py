from __future__ import annotations

import argparse
import json
import logging
import os
import sys
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

from generate_v2_evidence_bundle import DEFAULT_OUTPUT_DIR, build_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a complete V2 trial simulation with a generated PDF evidence bundle."
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the demo PDF evidence bundle will be generated.",
    )
    parser.add_argument(
        "--open-preview",
        action="store_true",
        help="Open the generated V2 HTML hearing record in the default browser.",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use the configured LLM provider to polish high-value V2 dialogue turns.",
    )
    parser.add_argument(
        "--llm-provider",
        default="",
        help="Optional provider override for this run, for example deepseek.",
    )
    parser.add_argument(
        "--llm-max-turns",
        type=int,
        default=12,
        help="Maximum number of V2 turns to polish with the LLM.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.use_llm:
        os.environ["AI_COURT_V2_LLM_ENABLED"] = "true"
        os.environ["AI_COURT_V2_LLM_MAX_TURNS"] = str(args.llm_max_turns)
    if args.llm_provider:
        os.environ["AI_COURT_LLM_PROVIDER"] = args.llm_provider

    from apps.api.app.main import app
    from packages.orchestration.python.ai_court_orchestration.v2_service import (
        get_courtroom_v2_runtime_service,
    )

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    manifest = build_bundle(args.evidence_dir)

    client = TestClient(app)
    create_response = client.post(
        "/api/v1/cases",
        json={
            "title": "Tranh chấp hợp đồng mua bán xe máy có bộ chứng cứ đầy đủ",
            "case_type": "civil_contract_dispute",
            "language": "vi",
            "narrative": manifest["narrative"],
            "attachments": [],
        },
    )
    create_response.raise_for_status()
    case_id = create_response.json()["case"]["case_id"]

    for document in manifest["documents"]:
        pdf_path = Path(document["path"])
        with pdf_path.open("rb") as handle:
            upload_response = client.post(
                f"/api/v1/cases/{case_id}/attachments",
                data={"note": document["note"]},
                files={"file": (document["filename"], handle, "application/pdf")},
            )
        upload_response.raise_for_status()

    parse_response = client.post(f"/api/v1/cases/{case_id}/parse")
    parse_response.raise_for_status()

    start_response = client.post(
        f"/api/v1/cases/{case_id}/trial-v2/start",
        params={"human_review_mode": "optional"},
    )
    start_response.raise_for_status()
    trial = start_response.json()

    for _ in range(20):
        if trial["current_stage"] == "closing_record":
            break
        advance_response = client.post(f"/api/v1/cases/{case_id}/trial-v2/advance", json={})
        advance_response.raise_for_status()
        trial = advance_response.json()
    else:
        raise RuntimeError("V2 trial did not reach closing_record within 20 advances.")

    markdown_response = client.post(f"/api/v1/cases/{case_id}/trial-v2/record/markdown")
    markdown_response.raise_for_status()
    html_response = client.post(f"/api/v1/cases/{case_id}/trial-v2/record/html")
    html_response.raise_for_status()

    decision = trial.get("simulated_decision") or {}
    guard = trial.get("decision_guard") or {}
    quality = trial.get("dialogue_quality") or {}
    runtime_service = get_courtroom_v2_runtime_service()
    summary = {
        "case_id": case_id,
        "evidence_bundle_dir": str(args.evidence_dir),
        "evidence_documents": [document["filename"] for document in manifest["documents"]],
        "llm_polish_enabled": args.use_llm,
        "llm_provider_used": runtime_service.last_llm_provider_label,
        "llm_polish_call_count": runtime_service.last_llm_polish_call_count,
        "llm_verifier_reject_count": runtime_service.last_llm_verifier_reject_count,
        "llm_verifier_reasons": runtime_service.last_llm_verifier_reasons,
        "v2_status": trial["status"],
        "current_stage": trial["current_stage"],
        "dialogue_turn_count": len(trial["dialogue_turns"]),
        "decision_disposition": decision.get("disposition"),
        "decision_risk_level": decision.get("risk_level"),
        "grounded_claim_ids": guard.get("grounded_claim_ids", []),
        "unresolved_items": guard.get("unresolved_items", []),
        "dialogue_quality": {
            "overlong_turn_ids": quality.get("overlong_turn_ids", []),
            "ungrounded_turn_ids": quality.get("ungrounded_turn_ids", []),
            "role_drift_warnings": quality.get("role_drift_warnings", []),
        },
        "record_markdown_path": markdown_response.json()["markdown_path"],
        "record_html_path": html_response.json()["html_path"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.open_preview:
        webbrowser.open(Path(summary["record_html_path"]).resolve().as_uri())


if __name__ == "__main__":
    main()
