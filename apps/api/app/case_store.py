from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from packages.shared.python.ai_court_shared.schemas import (
    AuditTrailResponse,
    CaseAttachment,
    CaseCreateRequest,
    CaseDetailResponse,
    CaseFileInput,
    CaseListResponse,
    CaseRecord,
    CaseState,
    CaseStatus,
    HearingSession,
    HumanReviewRecord,
    HtmlReportResponse,
    MarkdownReportResponse,
    SimulationResponse,
    V2TrialSession,
)

ROOT_DIR = Path(__file__).resolve().parents[3]
FIXTURES_DIR = ROOT_DIR / "packages" / "shared" / "fixtures"
RAW_CASES_DIR = ROOT_DIR / "data" / "raw" / "cases"
CASES_DIR = ROOT_DIR / "data" / "processed" / "cases"
DB_PATH = ROOT_DIR / "data" / "processed" / "ai_court.db"
CASE_ID_PATTERN = re.compile(r"CASE_(\d+)$")
ATTACHMENT_ID_PATTERN = re.compile(r"ATT_(\d+)$")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_storage() -> None:
    RAW_CASES_DIR.mkdir(parents=True, exist_ok=True)
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                case_type TEXT NOT NULL,
                language TEXT NOT NULL,
                narrative TEXT NOT NULL,
                status TEXT NOT NULL,
                attachments_json TEXT NOT NULL,
                parsed_state_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(cases)").fetchall()
        }
        if "review_record_json" not in columns:
            connection.execute("ALTER TABLE cases ADD COLUMN review_record_json TEXT")
        if "report_markdown_path" not in columns:
            connection.execute("ALTER TABLE cases ADD COLUMN report_markdown_path TEXT")


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _case_dir(case_id: str) -> Path:
    return CASES_DIR / case_id


def _raw_case_dir(case_id: str) -> Path:
    return RAW_CASES_DIR / case_id


def _attachments_dir(case_id: str) -> Path:
    return _raw_case_dir(case_id) / "attachments"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_fixture(name: str) -> dict:
    return _read_json(FIXTURES_DIR / name)


def _serialize_attachments(attachments: list[CaseAttachment]) -> str:
    return json.dumps(
        [attachment.model_dump(mode="json") for attachment in attachments],
        ensure_ascii=False,
    )


def _deserialize_attachments(raw_value: str) -> list[CaseAttachment]:
    payload = json.loads(raw_value)
    return [CaseAttachment.model_validate(item) for item in payload]


def _snapshot_case_input(case_input: CaseFileInput) -> None:
    _write_json(_case_dir(case_input.case_id) / "case.json", case_input.model_dump(mode="json"))


def _snapshot_case_state(case_state: CaseState) -> None:
    _write_json(_case_dir(case_state.case_id) / "parsed.json", case_state.model_dump(mode="json"))


def _snapshot_simulation_response(simulation_response: SimulationResponse) -> None:
    _write_json(
        _case_dir(simulation_response.case.case_id) / "simulation.json",
        simulation_response.model_dump(mode="json"),
    )


def _snapshot_hearing_session(hearing_session: HearingSession) -> None:
    _write_json(
        _case_dir(hearing_session.case.case_id) / "hearing_v1.json",
        hearing_session.model_dump(mode="json"),
    )


def _snapshot_v2_trial_session(trial_session: V2TrialSession) -> None:
    _write_json(
        _case_dir(trial_session.case.case_id) / "hearing_v2.json",
        trial_session.model_dump(mode="json"),
    )


def _snapshot_review_record(case_id: str, review_record: HumanReviewRecord) -> None:
    _write_json(
        _case_dir(case_id) / "review.json",
        review_record.model_dump(mode="json"),
    )


def _row_to_case_input(row: sqlite3.Row) -> CaseFileInput:
    return CaseFileInput(
        case_id=row["case_id"],
        title=row["title"],
        case_type=row["case_type"],
        language=row["language"],
        narrative=row["narrative"],
        attachments=_deserialize_attachments(row["attachments_json"]),
    )


def _row_to_case_state(row: sqlite3.Row) -> CaseState | None:
    raw_value = row["parsed_state_json"]
    if not raw_value:
        return None
    return CaseState.model_validate(json.loads(raw_value))


def _max_fixture_case_number() -> int:
    sample_case = _load_fixture("sample_case_01.case.json")
    match = CASE_ID_PATTERN.match(sample_case.get("case_id", ""))
    return int(match.group(1)) if match else 0


def _max_snapshot_case_number() -> int:
    if not CASES_DIR.exists():
        return 0
    max_number = 0
    for path in CASES_DIR.iterdir():
        if not path.is_dir():
            continue
        match = CASE_ID_PATTERN.match(path.name)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number


def _max_database_case_number(connection: sqlite3.Connection) -> int:
    rows = connection.execute("SELECT case_id FROM cases").fetchall()
    max_number = 0
    for row in rows:
        match = CASE_ID_PATTERN.match(row["case_id"])
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number


def reserve_next_case_id(connection: sqlite3.Connection) -> str:
    max_number = max(
        _max_fixture_case_number(),
        _max_snapshot_case_number(),
        _max_database_case_number(connection),
    )
    candidate = max_number + 1
    while True:
        case_id = f"CASE_{candidate:03d}"
        exists = connection.execute(
            "SELECT 1 FROM cases WHERE case_id = ? LIMIT 1",
            (case_id,),
        ).fetchone()
        if exists is None:
            return case_id
        candidate += 1


def create_case(request: CaseCreateRequest) -> CaseRecord:
    _ensure_storage()
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        case_id = reserve_next_case_id(connection)
        case_input = CaseFileInput(
            case_id=case_id,
            title=request.title,
            case_type=request.case_type,
            language=request.language,
            narrative=request.narrative,
            attachments=request.attachments,
        )
        now = _utc_now()
        connection.execute(
            """
            INSERT INTO cases (
                case_id, title, case_type, language, narrative, status,
                attachments_json, parsed_state_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_input.case_id,
                case_input.title,
                case_input.case_type,
                case_input.language,
                case_input.narrative,
                CaseStatus.DRAFT,
                _serialize_attachments(case_input.attachments),
                None,
                now,
                now,
            ),
        )
        connection.commit()
    _snapshot_case_input(case_input)
    return CaseRecord(
        case_id=case_input.case_id,
        title=case_input.title,
        case_type=case_input.case_type,
        language=case_input.language,
        status=CaseStatus.DRAFT,
        attachment_count=len(case_input.attachments),
    )


def build_case_record(case_input: CaseFileInput, case_state: CaseState | None = None) -> CaseRecord:
    status = case_state.status if case_state is not None else CaseStatus.DRAFT
    return CaseRecord(
        case_id=case_input.case_id,
        title=case_input.title,
        case_type=case_input.case_type,
        language=case_input.language,
        status=status,
        attachment_count=len(case_input.attachments),
    )


def load_case_input(case_id: str) -> CaseFileInput | None:
    _ensure_storage()
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM cases WHERE case_id = ?",
            (case_id,),
        ).fetchone()
    if row is not None:
        return _row_to_case_input(row)

    sample_case = _load_fixture("sample_case_01.case.json")
    if sample_case.get("case_id") == case_id:
        return CaseFileInput.model_validate(sample_case)
    return None


def save_case_state(case_state: CaseState) -> None:
    _ensure_storage()
    with _connect() as connection:
        connection.execute(
            """
            UPDATE cases
            SET status = ?, parsed_state_json = ?, updated_at = ?
            WHERE case_id = ?
            """,
            (
                case_state.status,
                json.dumps(case_state.model_dump(mode="json"), ensure_ascii=False),
                _utc_now(),
                case_state.case_id,
            ),
        )
        connection.commit()
    _snapshot_case_state(case_state)


def load_case_state(case_id: str) -> CaseState | None:
    _ensure_storage()
    with _connect() as connection:
        row = connection.execute(
            "SELECT parsed_state_json FROM cases WHERE case_id = ?",
            (case_id,),
        ).fetchone()
    if row is not None and row["parsed_state_json"]:
        return CaseState.model_validate(json.loads(row["parsed_state_json"]))

    sample_case = _load_fixture("sample_case_01.parse.json")
    if sample_case.get("case_id") == case_id:
        return CaseState.model_validate(sample_case)
    return None


def load_case_detail(case_id: str) -> CaseDetailResponse | None:
    case_input = load_case_input(case_id)
    if case_input is None:
        return None
    case_state = load_case_state(case_id)
    return CaseDetailResponse(
        record=build_case_record(case_input, case_state),
        case_input=case_input,
        parsed_case=case_state,
    )


def save_simulation_response(simulation_response: SimulationResponse) -> None:
    save_case_state(simulation_response.case)
    _snapshot_simulation_response(simulation_response)


def load_simulation_response(case_id: str) -> SimulationResponse | None:
    path = _case_dir(case_id) / "simulation.json"
    if path.exists():
        return SimulationResponse.model_validate(_read_json(path))

    sample_simulation = _load_fixture("sample_case_01.simulation.json")
    if sample_simulation.get("case", {}).get("case_id") == case_id:
        return SimulationResponse.model_validate(sample_simulation)
    return None


def save_hearing_session(hearing_session: HearingSession) -> None:
    save_case_state(hearing_session.case)
    _snapshot_hearing_session(hearing_session)


def load_hearing_session(case_id: str) -> HearingSession | None:
    path = _case_dir(case_id) / "hearing_v1.json"
    if path.exists():
        return HearingSession.model_validate(_read_json(path))

    sample_hearing = _load_fixture("sample_case_01.v1_hearing_session.json")
    if sample_hearing.get("case", {}).get("case_id") == case_id:
        return HearingSession.model_validate(sample_hearing)
    return None


def save_v2_trial_session(trial_session: V2TrialSession) -> None:
    save_case_state(trial_session.case)
    _snapshot_v2_trial_session(trial_session)


def load_v2_trial_session(case_id: str) -> V2TrialSession | None:
    path = _case_dir(case_id) / "hearing_v2.json"
    if path.exists():
        return V2TrialSession.model_validate(_read_json(path))

    sample_trial = _load_fixture("sample_case_01.v2_trial_session.json")
    if sample_trial.get("case", {}).get("case_id") == case_id:
        return V2TrialSession.model_validate(sample_trial)
    return None


def load_audit_trail(case_id: str) -> AuditTrailResponse | None:
    simulation_response = load_simulation_response(case_id)
    if simulation_response is None:
        return None
    return AuditTrailResponse(
        case_id=case_id,
        audit_trail=simulation_response.audit_trail,
        human_review=simulation_response.human_review,
    )


def load_review_record(case_id: str) -> HumanReviewRecord | None:
    _ensure_storage()
    with _connect() as connection:
        row = connection.execute(
            "SELECT review_record_json FROM cases WHERE case_id = ?",
            (case_id,),
        ).fetchone()
    if row is not None and row["review_record_json"]:
        return HumanReviewRecord.model_validate(json.loads(row["review_record_json"]))
    path = _case_dir(case_id) / "review.json"
    if path.exists():
        return HumanReviewRecord.model_validate(_read_json(path))
    return None


def list_cases() -> CaseListResponse:
    _ensure_storage()
    records: list[CaseRecord] = []
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT case_id, title, case_type, language, narrative, status, attachments_json, parsed_state_json
            FROM cases
            ORDER BY created_at DESC
            """
        ).fetchall()
    for row in rows:
        case_input = _row_to_case_input(row)
        case_state = _row_to_case_state(row)
        records.append(build_case_record(case_input, case_state))
    return CaseListResponse(cases=records)


def save_review_record(case_id: str, review_record: HumanReviewRecord) -> None:
    _ensure_storage()
    with _connect() as connection:
        connection.execute(
            """
            UPDATE cases
            SET review_record_json = ?, status = ?, updated_at = ?
            WHERE case_id = ?
            """,
            (
                json.dumps(review_record.model_dump(mode="json"), ensure_ascii=False),
                review_record.status_after,
                _utc_now(),
                case_id,
            ),
        )
        connection.commit()
    _snapshot_review_record(case_id, review_record)


def save_markdown_report(case_id: str, markdown: str) -> str:
    _ensure_storage()
    path = _case_dir(case_id) / "report.md"
    _write_text(path, markdown)
    with _connect() as connection:
        connection.execute(
            """
            UPDATE cases
            SET report_markdown_path = ?, updated_at = ?
            WHERE case_id = ?
            """,
            (
                str(path),
                _utc_now(),
                case_id,
            ),
        )
        connection.commit()
    return str(path)


def save_hearing_record_markdown(case_id: str, markdown: str) -> str:
    path = _case_dir(case_id) / "hearing_v1_record.md"
    _write_text(path, markdown)
    return str(path)


def save_hearing_record_html(case_id: str, html: str) -> str:
    path = _case_dir(case_id) / "hearing_v1_record.html"
    _write_text(path, html)
    return str(path)


def load_hearing_record_markdown(case_id: str) -> MarkdownReportResponse | None:
    hearing_session = load_hearing_session(case_id)
    if hearing_session is None:
        return None
    path = _case_dir(case_id) / "hearing_v1_record.md"
    if not path.exists():
        return None
    return MarkdownReportResponse(
        case_id=case_id,
        report_status=hearing_session.status,
        markdown_path=str(path),
        markdown=path.read_text(encoding="utf-8"),
    )


def load_hearing_record_html(case_id: str) -> HtmlReportResponse | None:
    hearing_session = load_hearing_session(case_id)
    if hearing_session is None:
        return None
    path = _case_dir(case_id) / "hearing_v1_record.html"
    if not path.exists():
        return None
    return HtmlReportResponse(
        case_id=case_id,
        report_status=hearing_session.status,
        html_path=str(path),
        html=path.read_text(encoding="utf-8"),
    )


def load_markdown_report(case_id: str) -> MarkdownReportResponse | None:
    _ensure_storage()
    simulation_response = load_simulation_response(case_id)
    if simulation_response is None:
        return None
    with _connect() as connection:
        row = connection.execute(
            "SELECT report_markdown_path FROM cases WHERE case_id = ?",
            (case_id,),
        ).fetchone()
    markdown_path = row["report_markdown_path"] if row is not None else None
    if not markdown_path:
        path = _case_dir(case_id) / "report.md"
        if not path.exists():
            return None
        markdown_path = str(path)
    path = Path(markdown_path)
    if not path.exists():
        return None
    return MarkdownReportResponse(
        case_id=case_id,
        report_status=simulation_response.case.status,
        markdown_path=str(path),
        markdown=path.read_text(encoding="utf-8"),
    )


def reserve_next_attachment_id(attachments: list[CaseAttachment]) -> str:
    max_number = 0
    for attachment in attachments:
        match = ATTACHMENT_ID_PATTERN.match(attachment.attachment_id)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return f"ATT_{max_number + 1:03d}"


def add_case_attachment(
    case_id: str,
    filename: str,
    media_type: str,
    note: str | None,
    local_path: str,
) -> CaseDetailResponse | None:
    _ensure_storage()
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM cases WHERE case_id = ?",
            (case_id,),
        ).fetchone()
        if row is None:
            return None

        case_input = _row_to_case_input(row)
        attachments = list(case_input.attachments)
        attachments.append(
            CaseAttachment(
                attachment_id=reserve_next_attachment_id(attachments),
                filename=filename,
                media_type=media_type,
                note=note,
                local_path=local_path,
            )
        )
        updated_case_input = CaseFileInput(
            case_id=case_input.case_id,
            title=case_input.title,
            case_type=case_input.case_type,
            language=case_input.language,
            narrative=case_input.narrative,
            attachments=attachments,
        )
        connection.execute(
            """
            UPDATE cases
            SET attachments_json = ?, status = ?, parsed_state_json = ?, updated_at = ?
            WHERE case_id = ?
            """,
            (
                _serialize_attachments(updated_case_input.attachments),
                CaseStatus.DRAFT,
                None,
                _utc_now(),
                case_id,
            ),
        )
        connection.commit()
    _snapshot_case_input(updated_case_input)
    parsed_snapshot = _case_dir(case_id) / "parsed.json"
    if parsed_snapshot.exists():
        parsed_snapshot.unlink()
    return load_case_detail(case_id)


def store_uploaded_attachment_file(case_id: str, filename: str, payload: bytes) -> str:
    _ensure_storage()
    safe_name = Path(filename).name or "attachment.bin"
    target_dir = _attachments_dir(case_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name
    if target_path.exists():
        stem = target_path.stem
        suffix = target_path.suffix
        counter = 1
        while True:
            candidate = target_dir / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                target_path = candidate
                break
            counter += 1
    target_path.write_bytes(payload)
    return str(target_path)
