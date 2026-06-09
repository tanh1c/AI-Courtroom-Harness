from apps.api.app.main import app
from ai_court_orchestration.service import get_courtroom_simulation_service
from ai_court_orchestration.v1_service import get_courtroom_v1_runtime_service
from ai_court_orchestration.v2_service import get_courtroom_v2_runtime_service
from ai_court_reporting.service import get_markdown_report_service
from ai_court_retrieval.service import get_local_legal_retrieval_service
from ai_court_shared.schemas import CaseFileInput
from ai_court_verification.service import get_verification_service


def test_backend_packages_import_from_installed_package_roots() -> None:
    assert app.title == "AI Courtroom Harness API"
    assert get_courtroom_simulation_service() is not None
    assert get_courtroom_v1_runtime_service() is not None
    assert get_courtroom_v2_runtime_service() is not None
    assert get_markdown_report_service() is not None
    assert get_local_legal_retrieval_service() is not None
    assert get_verification_service() is not None
    assert CaseFileInput(
        case_id="CASE_TEST",
        case_type="civil_contract_dispute",
        title="Import smoke test",
        narrative="The claimant alleges a contract breach after non-payment.",
    )
