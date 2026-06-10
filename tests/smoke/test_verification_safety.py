from ai_court_shared.schemas import (
    AgentName,
    CaseState,
    CaseStatus,
    CaseType,
    Citation,
    Claim,
    ClaimConfidence,
    EffectiveStatus,
    Evidence,
    EvidenceStatus,
    EvidenceType,
    FactCheckResult,
    FinalReport,
    HumanReviewGate,
    JudgeSummary,
    RetrievalStrategy,
    CitationVerificationResult,
    SimulationResponse,
    TrialMinutes,
)
from ai_court_verification.service import get_verification_service


def build_negative_simulation() -> SimulationResponse:
    expired_citation = Citation(
        citation_id="CITE_EXPIRED",
        doc_id="DOC_001",
        chunk_id="CHUNK_001",
        title="Expired civil code article",
        article="Điều 001",
        content="Expired legal basis used only for safety testing.",
        retrieval_score=1.0,
        retrieval_method=RetrievalStrategy.BM25_LOCAL,
        effective_status=EffectiveStatus.EXPIRED,
        raw_effective_status="hết hiệu lực",
        source="fixture:test",
        provenance={"source": "fixture:test"},
    )
    case = CaseState(
        case_id="CASE_SAFETY_NEGATIVE",
        title="Safety negative fixture",
        case_type=CaseType.CIVIL_CONTRACT_DISPUTE,
        evidence=[
            Evidence(
                evidence_id="EVID_DISPUTED",
                type=EvidenceType.STATEMENT,
                content="Disputed narrative evidence.",
                source="narrative",
                status=EvidenceStatus.DISPUTED,
                used_by=[AgentName.PLAINTIFF_AGENT.value],
                challenged_by=[AgentName.DEFENSE_AGENT.value],
            )
        ],
        claims=[
            Claim(
                claim_id="CLAIM_UNSUPPORTED",
                speaker=AgentName.PLAINTIFF_AGENT,
                content="Unsupported claim without evidence.",
                evidence_ids=[],
                citation_ids=["CITE_EXPIRED", "CITE_NOT_RETRIEVED"],
                confidence=ClaimConfidence.HIGH,
            )
        ],
        citations=[expired_citation],
        status=CaseStatus.SIMULATED,
    )
    return SimulationResponse(
        case=case,
        fact_check=FactCheckResult(risk_level=ClaimConfidence.LOW),
        citation_verification=CitationVerificationResult(),
        audit_trail=[],
        human_review=HumanReviewGate(required=False, blocked=False),
        judge_summary=JudgeSummary(
            summary="Fixture summary.",
            recommended_human_review=False,
        ),
        trial_minutes=TrialMinutes(
            case_id=case.case_id,
            minutes_markdown="Fixture minutes.",
        ),
        final_report=FinalReport(
            case_id=case.case_id,
            case_summary="Fixture report.",
            disclaimer="Non-binding simulation fixture.",
        ),
    )


def test_verification_flags_negative_safety_cases() -> None:
    verified = get_verification_service().verify(build_negative_simulation())

    assert verified.case.status == CaseStatus.REVIEW_REQUIRED
    assert verified.human_review.required is True
    assert verified.human_review.blocked is True
    assert "CLAIM_UNSUPPORTED" in verified.fact_check.unsupported_claims
    assert "CLAIM_UNSUPPORTED" in verified.fact_check.citation_mismatches
    assert "CITE_EXPIRED" in verified.citation_verification.rejected_citations
    assert "CITE_NOT_RETRIEVED" in verified.citation_verification.rejected_citations
    assert verified.fact_check.risk_level == ClaimConfidence.HIGH
    assert any(finding.severity == ClaimConfidence.HIGH for finding in verified.fact_check.findings)
    assert any(finding.citation_id == "CITE_EXPIRED" for finding in verified.citation_verification.findings)
    assert any(finding.citation_id == "CITE_NOT_RETRIEVED" for finding in verified.citation_verification.findings)
    assert any(event.severity == ClaimConfidence.HIGH for event in verified.audit_trail)
