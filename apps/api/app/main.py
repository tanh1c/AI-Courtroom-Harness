from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.shared.python.ai_court_shared.schemas import (
    CaseCreateRequest,
    CaseCreateResponse,
    CaseFileInput,
    CaseState,
    ParseCaseResponse,
    ReportResponse,
    SimulationResponse,
)
FIXTURES_DIR = ROOT_DIR / "packages" / "shared" / "fixtures"


def load_fixture(name: str) -> dict:
    with (FIXTURES_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


app = FastAPI(
    title="AI Courtroom Harness API",
    version="0.1.0",
    description="Phase 0 mock API used to lock shared contracts and unblock parallel work.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/fixtures/sample-case", response_model=CaseFileInput)
def get_sample_case() -> CaseFileInput:
    return CaseFileInput.model_validate(load_fixture("sample_case_01.case.json"))


@app.post("/api/v1/cases", response_model=CaseCreateResponse)
def create_case(_: CaseCreateRequest) -> CaseCreateResponse:
    payload = load_fixture("sample_case_01.create.response.json")
    return CaseCreateResponse.model_validate(payload)


@app.post("/api/v1/cases/{case_id}/parse", response_model=ParseCaseResponse)
def parse_case(case_id: str) -> ParseCaseResponse:
    payload = load_fixture("sample_case_01.parse.json")
    payload["case_id"] = case_id
    return ParseCaseResponse(case=CaseState.model_validate(payload))


@app.post("/api/v1/legal-search")
def legal_search(_: dict) -> dict:
    simulation = load_fixture("sample_case_01.simulation.json")
    return {
        "citations": simulation["case"]["citations"],
        "query_strategy": "fixture_stub",
    }


@app.post("/api/v1/cases/{case_id}/simulate", response_model=SimulationResponse)
def simulate_case(case_id: str) -> SimulationResponse:
    payload = load_fixture("sample_case_01.simulation.json")
    payload["case"]["case_id"] = case_id
    payload["trial_minutes"]["case_id"] = case_id
    payload["final_report"]["case_id"] = case_id
    return SimulationResponse.model_validate(payload)


@app.get("/api/v1/reports/{case_id}", response_model=ReportResponse)
def get_report(case_id: str) -> ReportResponse:
    payload = load_fixture("sample_case_01.report.json")
    payload["case_id"] = case_id
    payload["report"]["case_id"] = case_id
    return ReportResponse.model_validate(payload)
