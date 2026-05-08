from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from .case_parser import parse_case_input
from .case_store import (
    add_case_attachment,
    create_case as create_case_record,
    load_case_detail,
    load_case_input,
    load_case_state,
    list_cases,
    save_case_state,
    store_uploaded_attachment_file,
)
from packages.retrieval.python.ai_court_retrieval.service import (
    get_local_legal_retrieval_service,
)
from packages.shared.python.ai_court_shared.schemas import (
    CaseCreateRequest,
    CaseCreateResponse,
    CaseDetailResponse,
    CaseFileInput,
    CaseListResponse,
    CaseState,
    LegalSearchRequest,
    LegalSearchResponse,
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
    description="Phase 1 retrieval plus Phase 2 case intake baseline API for AI Courtroom Harness.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/fixtures/sample-case", response_model=CaseFileInput)
def get_sample_case() -> CaseFileInput:
    return CaseFileInput.model_validate(load_fixture("sample_case_01.case.json"))


@app.get("/api/v1/cases", response_model=CaseListResponse)
def get_cases() -> CaseListResponse:
    return list_cases()


@app.post("/api/v1/cases", response_model=CaseCreateResponse)
def create_case(request: CaseCreateRequest) -> CaseCreateResponse:
    record = create_case_record(request)
    return CaseCreateResponse(case=record)


@app.get("/api/v1/cases/{case_id}", response_model=CaseDetailResponse)
def get_case_detail(case_id: str) -> CaseDetailResponse:
    case_detail = load_case_detail(case_id)
    if case_detail is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return case_detail


@app.post("/api/v1/cases/{case_id}/attachments", response_model=CaseDetailResponse)
async def upload_case_attachment(
    case_id: str,
    file: UploadFile = File(...),
    note: str | None = Form(default=None),
) -> CaseDetailResponse:
    case_input = load_case_input(case_id)
    if case_input is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    payload = await file.read()
    local_path = store_uploaded_attachment_file(case_id, file.filename, payload)
    case_detail = add_case_attachment(
        case_id=case_id,
        filename=file.filename,
        media_type=file.content_type or "application/octet-stream",
        note=note,
        local_path=local_path,
    )
    if case_detail is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return case_detail


@app.post("/api/v1/cases/{case_id}/parse", response_model=ParseCaseResponse)
def parse_case(case_id: str) -> ParseCaseResponse:
    case_input = load_case_input(case_id)
    if case_input is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    case_state = parse_case_input(case_input)
    save_case_state(case_state)
    return ParseCaseResponse(case=case_state)


@app.get("/api/v1/cases/{case_id}/state", response_model=ParseCaseResponse)
def get_case_state(case_id: str) -> ParseCaseResponse:
    case_state = load_case_state(case_id)
    if case_state is None:
        raise HTTPException(status_code=404, detail=f"Parsed case state not found: {case_id}")
    return ParseCaseResponse(case=case_state)


@app.post("/api/v1/legal-search", response_model=LegalSearchResponse)
def legal_search(request: LegalSearchRequest) -> LegalSearchResponse:
    service = get_local_legal_retrieval_service()
    return service.search(request)


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
