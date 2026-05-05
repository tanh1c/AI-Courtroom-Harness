from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.shared.python.ai_court_shared.schemas import (
    CaseFileInput,
    CaseState,
    ParseCaseResponse,
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


@app.post("/api/v1/cases/parse", response_model=ParseCaseResponse)
def parse_case(_: CaseFileInput) -> ParseCaseResponse:
    payload = load_fixture("sample_case_01.parse.json")
    return ParseCaseResponse(case=CaseState.model_validate(payload))


@app.post("/api/v1/legal-search")
def legal_search(_: dict) -> dict:
    simulation = load_fixture("sample_case_01.simulation.json")
    return {
        "citations": simulation["case"]["citations"],
        "query_strategy": "fixture_stub",
    }


@app.post("/api/v1/cases/simulate", response_model=SimulationResponse)
def simulate_case(_: dict) -> SimulationResponse:
    payload = load_fixture("sample_case_01.simulation.json")
    return SimulationResponse.model_validate(payload)
