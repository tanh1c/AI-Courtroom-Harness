from __future__ import annotations

import json
import re
from pathlib import Path

from packages.shared.python.ai_court_shared.schemas import (
    CaseCreateRequest,
    CaseDetailResponse,
    CaseFileInput,
    CaseRecord,
    CaseState,
    CaseStatus,
)

ROOT_DIR = Path(__file__).resolve().parents[3]
FIXTURES_DIR = ROOT_DIR / "packages" / "shared" / "fixtures"
CASES_DIR = ROOT_DIR / "data" / "processed" / "cases"
CASE_ID_PATTERN = re.compile(r"CASE_(\d+)$")


def _ensure_cases_dir() -> None:
    CASES_DIR.mkdir(parents=True, exist_ok=True)


def _case_dir(case_id: str) -> Path:
    return CASES_DIR / case_id


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_fixture(name: str) -> dict:
    return _read_json(FIXTURES_DIR / name)


def reserve_next_case_dir() -> tuple[str, Path]:
    _ensure_cases_dir()
    max_number = 0
    sample_case = _load_fixture("sample_case_01.case.json")
    sample_case_id = sample_case.get("case_id", "")
    match = CASE_ID_PATTERN.match(sample_case_id)
    if match:
        max_number = max(max_number, int(match.group(1)))
    for path in CASES_DIR.iterdir():
        if not path.is_dir():
            continue
        match = CASE_ID_PATTERN.match(path.name)
        if match:
            max_number = max(max_number, int(match.group(1)))
    candidate = max_number + 1
    while True:
        case_id = f"CASE_{candidate:03d}"
        case_dir = _case_dir(case_id)
        try:
            case_dir.mkdir(parents=True, exist_ok=False)
            return case_id, case_dir
        except FileExistsError:
            candidate += 1


def create_case(request: CaseCreateRequest) -> CaseRecord:
    case_id, case_dir = reserve_next_case_dir()
    case_input = CaseFileInput(
        case_id=case_id,
        title=request.title,
        case_type=request.case_type,
        language=request.language,
        narrative=request.narrative,
        attachments=request.attachments,
    )
    _write_json(case_dir / "case.json", case_input.model_dump(mode="json"))
    return CaseRecord(
        case_id=case_id,
        title=case_input.title,
        case_type=case_input.case_type,
        language=case_input.language,
        status=CaseStatus.DRAFT,
        attachment_count=len(case_input.attachments),
    )


def load_case_input(case_id: str) -> CaseFileInput | None:
    path = _case_dir(case_id) / "case.json"
    if path.exists():
        return CaseFileInput.model_validate(_read_json(path))

    sample_case = _load_fixture("sample_case_01.case.json")
    if sample_case.get("case_id") == case_id:
        return CaseFileInput.model_validate(sample_case)
    return None


def save_case_state(case_state: CaseState) -> None:
    _write_json(
        _case_dir(case_state.case_id) / "parsed.json",
        case_state.model_dump(mode="json"),
    )


def load_case_state(case_id: str) -> CaseState | None:
    path = _case_dir(case_id) / "parsed.json"
    if path.exists():
        return CaseState.model_validate(_read_json(path))

    sample_case = _load_fixture("sample_case_01.parse.json")
    if sample_case.get("case_id") == case_id:
        return CaseState.model_validate(sample_case)
    return None


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
