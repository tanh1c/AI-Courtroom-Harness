from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
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
    load_audit_trail,
    load_case_detail,
    load_case_input,
    load_case_state,
    load_hearing_session,
    load_hearing_record_html,
    load_hearing_record_markdown,
    load_markdown_report,
    load_review_record,
    load_simulation_response,
    load_v2_trial_session,
    list_cases,
    save_case_state,
    save_hearing_session,
    save_hearing_record_html,
    save_hearing_record_markdown,
    save_markdown_report,
    save_review_record,
    save_simulation_response,
    save_v2_trial_session,
    store_uploaded_attachment_file,
)
from packages.orchestration.python.ai_court_orchestration.service import (
    get_courtroom_simulation_service,
)
from packages.orchestration.python.ai_court_orchestration.v1_service import (
    HearingRuntimeError,
    get_courtroom_v1_runtime_service,
)
from packages.orchestration.python.ai_court_orchestration.v2_service import (
    TrialRuntimeError,
    get_courtroom_v2_runtime_service,
)
from packages.reporting.python.ai_court_reporting.service import (
    get_html_report_service,
    get_markdown_report_service,
    get_v1_hearing_record_service,
)
from packages.retrieval.python.ai_court_retrieval.service import (
    get_local_legal_retrieval_service,
)
from packages.shared.python.ai_court_shared.schemas import (
    AuditEvent,
    AuditStage,
    AuditTrailResponse,
    CaseCreateRequest,
    CaseCreateResponse,
    CaseDetailResponse,
    CaseFileInput,
    CaseListResponse,
    CaseStatus,
    ClaimConfidence,
    HumanReviewGate,
    HearingAdvanceRequest,
    HearingEvidenceChallengesResponse,
    HearingOutcomeResponse,
    HearingSession,
    HearingVerificationResponse,
    HtmlReportResponse,
    HumanReviewRecord,
    HumanReviewRequest,
    HumanReviewResponse,
    HumanReviewMode,
    LegalSearchRequest,
    LegalSearchResponse,
    MarkdownReportResponse,
    ParseCaseResponse,
    ReportResponse,
    SimulationResponse,
    V2TrialAdvanceRequest,
    V2TrialSession,
)
from packages.verification.python.ai_court_verification.service import (
    get_verification_service,
)
FIXTURES_DIR = ROOT_DIR / "packages" / "shared" / "fixtures"


def load_fixture(name: str) -> dict:
    with (FIXTURES_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def next_audit_event_id(events: list[AuditEvent]) -> str:
    return f"AUDIT_{len(events) + 1:03d}"


def resolve_human_review(
    case_id: str,
    request: HumanReviewRequest,
) -> HumanReviewResponse:
    simulation_response = load_simulation_response(case_id)
    if simulation_response is None:
        raise HTTPException(status_code=404, detail=f"Simulation not found: {case_id}")

    updated = SimulationResponse.model_validate(simulation_response.model_dump(mode="json"))
    checklist = list(dict.fromkeys(
        updated.human_review.checklist
        + updated.final_report.human_review_checklist
        + request.checklist_updates
    ))

    if request.decision.value == "approve":
        report_status = CaseStatus.REPORT_READY
        updated.human_review = HumanReviewGate(
            required=False,
            blocked=False,
            reasons=[],
            checklist=checklist,
        )
        severity = ClaimConfidence.LOW
        message = f"Human reviewer {request.reviewer_name} approved the report for export."
    else:
        report_status = CaseStatus.REVIEW_REQUIRED
        rejection_reasons = list(updated.human_review.reasons)
        rejection_reasons.append("Human reviewer rejected the current report and requested revisions.")
        if request.notes:
            rejection_reasons.append(f"Reviewer note: {request.notes}")
        updated.human_review = HumanReviewGate(
            required=True,
            blocked=True,
            reasons=list(dict.fromkeys(rejection_reasons)),
            checklist=checklist,
        )
        severity = ClaimConfidence.HIGH
        message = f"Human reviewer {request.reviewer_name} rejected the report pending revisions."

    updated.case.status = report_status
    updated.final_report.human_review_checklist = checklist
    updated.audit_trail.append(
        AuditEvent(
            event_id=next_audit_event_id(updated.audit_trail),
            stage=AuditStage.HUMAN_REVIEW,
            severity=severity,
            message=message,
        )
    )

    review_record = HumanReviewRecord(
        reviewer_name=request.reviewer_name,
        decision=request.decision,
        notes=request.notes,
        checklist_updates=request.checklist_updates,
        resolved_at=utc_now(),
        status_after=report_status,
    )

    save_simulation_response(updated)
    save_review_record(case_id, review_record)
    return HumanReviewResponse(
        case_id=case_id,
        report_status=report_status,
        human_review=updated.human_review,
        review_record=review_record,
        report=updated.final_report,
    )


app = FastAPI(
    title="AI Courtroom Harness API",
    version="0.1.0",
    description="Phase 1 retrieval, Phase 2 intake, and Phase 3 simulation baseline API for AI Courtroom Harness.",
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


@app.get("/api/v1/cases/{case_id}/audit", response_model=AuditTrailResponse)
def get_case_audit(case_id: str) -> AuditTrailResponse:
    audit_response = load_audit_trail(case_id)
    if audit_response is None:
        raise HTTPException(status_code=404, detail=f"Audit trail not found: {case_id}")
    return audit_response


@app.post("/api/v1/legal-search", response_model=LegalSearchResponse)
def legal_search(request: LegalSearchRequest) -> LegalSearchResponse:
    service = get_local_legal_retrieval_service()
    return service.search(request)


@app.post("/api/v1/cases/{case_id}/simulate", response_model=SimulationResponse)
def simulate_case(case_id: str) -> SimulationResponse:
    case_state = load_case_state(case_id)
    if case_state is None:
        raise HTTPException(status_code=404, detail=f"Parsed case state not found: {case_id}")
    simulation_service = get_courtroom_simulation_service()
    verification_service = get_verification_service()
    simulation_response = verification_service.verify(simulation_service.simulate(case_state))
    save_simulation_response(simulation_response)
    return simulation_response


@app.post("/api/v1/cases/{case_id}/hearing/start", response_model=HearingSession)
def start_v1_hearing(case_id: str) -> HearingSession:
    case_state = load_case_state(case_id)
    if case_state is None:
        raise HTTPException(status_code=404, detail=f"Parsed case state not found: {case_id}")

    hearing_session = get_courtroom_v1_runtime_service().start(case_state)
    save_hearing_session(hearing_session)
    return hearing_session


@app.post("/api/v1/cases/{case_id}/hearing/advance", response_model=HearingSession)
def advance_v1_hearing(
    case_id: str,
    request: HearingAdvanceRequest | None = None,
) -> HearingSession:
    hearing_session = load_hearing_session(case_id)
    if hearing_session is None:
        raise HTTPException(status_code=404, detail=f"V1 hearing session not found: {case_id}")

    try:
        updated = get_courtroom_v1_runtime_service().advance(
            hearing_session,
            expected_stage=request.expected_stage if request is not None else None,
        )
    except HearingRuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    save_hearing_session(updated)
    return updated


@app.get("/api/v1/cases/{case_id}/hearing", response_model=HearingSession)
def get_v1_hearing(case_id: str) -> HearingSession:
    hearing_session = load_hearing_session(case_id)
    if hearing_session is None:
        raise HTTPException(status_code=404, detail=f"V1 hearing session not found: {case_id}")
    return hearing_session


@app.post("/api/v1/cases/{case_id}/trial-v2/start", response_model=V2TrialSession)
def start_v2_trial(
    case_id: str,
    human_review_mode: HumanReviewMode = HumanReviewMode.OPTIONAL,
) -> V2TrialSession:
    case_state = load_case_state(case_id)
    if case_state is None:
        raise HTTPException(status_code=404, detail=f"Parsed case state not found: {case_id}")

    trial_session = get_courtroom_v2_runtime_service().start(
        case_state,
        human_review_mode=human_review_mode,
    )
    save_v2_trial_session(trial_session)
    return trial_session


@app.post("/api/v1/cases/{case_id}/trial-v2/advance", response_model=V2TrialSession)
def advance_v2_trial(
    case_id: str,
    request: V2TrialAdvanceRequest | None = None,
) -> V2TrialSession:
    trial_session = load_v2_trial_session(case_id)
    if trial_session is None:
        raise HTTPException(status_code=404, detail=f"V2 trial session not found: {case_id}")

    try:
        updated = get_courtroom_v2_runtime_service().advance(
            trial_session,
            expected_stage=request.expected_stage if request is not None else None,
        )
    except TrialRuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    save_v2_trial_session(updated)
    return updated


@app.get("/api/v1/cases/{case_id}/trial-v2", response_model=V2TrialSession)
def get_v2_trial(case_id: str) -> V2TrialSession:
    trial_session = load_v2_trial_session(case_id)
    if trial_session is None:
        raise HTTPException(status_code=404, detail=f"V2 trial session not found: {case_id}")
    return trial_session


@app.get("/api/v1/cases/{case_id}/evidence/challenges", response_model=HearingEvidenceChallengesResponse)
def get_v1_evidence_challenges(case_id: str) -> HearingEvidenceChallengesResponse:
    hearing_session = load_hearing_session(case_id)
    if hearing_session is None:
        raise HTTPException(status_code=404, detail=f"V1 hearing session not found: {case_id}")
    evidence_agent_turns = [
        turn for turn in hearing_session.turns if turn.agent.value == "evidence_agent"
    ]
    return HearingEvidenceChallengesResponse(
        case_id=case_id,
        challenges=hearing_session.evidence_challenges,
        evidence_agent_turns=evidence_agent_turns,
    )


@app.get("/api/v1/cases/{case_id}/verification", response_model=HearingVerificationResponse)
def get_v1_verification(case_id: str) -> HearingVerificationResponse:
    hearing_session = load_hearing_session(case_id)
    if hearing_session is None:
        raise HTTPException(status_code=404, detail=f"V1 hearing session not found: {case_id}")
    verification_turns = [
        turn
        for turn in hearing_session.turns
        if turn.agent.value in {"fact_check_agent", "citation_verifier_agent"}
    ]
    verification_tool_call_ids = {
        tool_call_id
        for turn in verification_turns
        for tool_call_id in turn.tool_call_ids
    }
    return HearingVerificationResponse(
        case_id=case_id,
        fact_check=hearing_session.fact_check,
        citation_verification=hearing_session.citation_verification,
        verification_turns=verification_turns,
        tool_calls=[
            tool_call
            for tool_call in hearing_session.tool_calls
            if tool_call.tool_call_id in verification_tool_call_ids
        ],
    )


@app.get("/api/v1/cases/{case_id}/outcome", response_model=HearingOutcomeResponse)
def get_v1_outcome(case_id: str) -> HearingOutcomeResponse:
    hearing_session = load_hearing_session(case_id)
    if hearing_session is None:
        raise HTTPException(status_code=404, detail=f"V1 hearing session not found: {case_id}")
    preliminary_turns = [
        turn
        for turn in hearing_session.turns
        if turn.hearing_stage.value == "preliminary_assessment"
    ]
    return HearingOutcomeResponse(
        case_id=case_id,
        outcome_candidates=hearing_session.outcome_candidates,
        preliminary_assessment_turns=preliminary_turns,
        harness_violations=hearing_session.harness_violations,
        human_review=hearing_session.human_review,
    )


@app.post("/api/v1/cases/{case_id}/hearing/record/markdown", response_model=MarkdownReportResponse)
def export_v1_hearing_record_markdown(case_id: str) -> MarkdownReportResponse:
    hearing_session = load_hearing_session(case_id)
    if hearing_session is None:
        raise HTTPException(status_code=404, detail=f"V1 hearing session not found: {case_id}")
    markdown = get_v1_hearing_record_service().render(hearing_session)
    markdown_path = save_hearing_record_markdown(case_id, markdown)
    return MarkdownReportResponse(
        case_id=case_id,
        report_status=hearing_session.status,
        markdown_path=markdown_path,
        markdown=markdown,
    )


@app.get("/api/v1/cases/{case_id}/hearing/record/markdown", response_model=MarkdownReportResponse)
def get_v1_hearing_record_markdown(case_id: str) -> MarkdownReportResponse:
    report = load_hearing_record_markdown(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"V1 hearing markdown record not found: {case_id}")
    return report


@app.post("/api/v1/cases/{case_id}/hearing/record/html", response_model=HtmlReportResponse)
def export_v1_hearing_record_html(case_id: str) -> HtmlReportResponse:
    hearing_session = load_hearing_session(case_id)
    if hearing_session is None:
        raise HTTPException(status_code=404, detail=f"V1 hearing session not found: {case_id}")
    markdown_report = load_hearing_record_markdown(case_id)
    markdown = (
        markdown_report.markdown
        if markdown_report is not None
        else get_v1_hearing_record_service().render(hearing_session)
    )
    html = get_html_report_service().render(
        title=f"V1 Simulated Hearing Record - {case_id}",
        markdown_text=markdown,
    )
    if markdown_report is None:
        save_hearing_record_markdown(case_id, markdown)
    html_path = save_hearing_record_html(case_id, html)
    return HtmlReportResponse(
        case_id=case_id,
        report_status=hearing_session.status,
        html_path=html_path,
        html=html,
    )


@app.get("/api/v1/cases/{case_id}/hearing/record/html", response_model=HtmlReportResponse)
def get_v1_hearing_record_html(case_id: str) -> HtmlReportResponse:
    report = load_hearing_record_html(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"V1 hearing HTML record not found: {case_id}")
    return report


@app.post("/api/v1/cases/{case_id}/review", response_model=HumanReviewResponse)
def review_case(case_id: str, request: HumanReviewRequest) -> HumanReviewResponse:
    return resolve_human_review(case_id, request)


@app.get("/api/v1/reports/{case_id}", response_model=ReportResponse)
def get_report(case_id: str) -> ReportResponse:
    simulation_response = load_simulation_response(case_id)
    if simulation_response is not None:
        return ReportResponse(
            case_id=case_id,
            report_status=simulation_response.case.status,
            generated_from_turns=simulation_response.trial_minutes.turn_ids,
            report=simulation_response.final_report,
        )

    payload = load_fixture("sample_case_01.report.json")
    payload["case_id"] = case_id
    payload["report"]["case_id"] = case_id
    return ReportResponse.model_validate(payload)


@app.post("/api/v1/reports/{case_id}/markdown", response_model=MarkdownReportResponse)
def export_markdown_report(case_id: str) -> MarkdownReportResponse:
    simulation_response = load_simulation_response(case_id)
    if simulation_response is None:
        raise HTTPException(status_code=404, detail=f"Simulation not found: {case_id}")
    if simulation_response.case.status != CaseStatus.REPORT_READY:
        raise HTTPException(
            status_code=409,
            detail=f"Report is not ready for markdown export: {simulation_response.case.status.value}",
        )

    review_record = load_review_record(case_id)
    service = get_markdown_report_service()
    markdown = service.render(simulation_response, review_record)
    markdown_path = save_markdown_report(case_id, markdown)
    return MarkdownReportResponse(
        case_id=case_id,
        report_status=simulation_response.case.status,
        markdown_path=markdown_path,
        markdown=markdown,
    )


@app.get("/api/v1/reports/{case_id}/markdown", response_model=MarkdownReportResponse)
def get_markdown_export(case_id: str) -> MarkdownReportResponse:
    report = load_markdown_report(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Markdown report not found: {case_id}")
    return report
