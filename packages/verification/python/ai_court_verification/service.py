from __future__ import annotations

from functools import lru_cache

from packages.shared.python.ai_court_shared.schemas import (
    AuditEvent,
    AuditStage,
    CaseStatus,
    ClaimConfidence,
    Citation,
    CitationVerificationResult,
    FactCheckResult,
    HumanReviewGate,
    SimulationResponse,
)


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


class VerificationService:
    def verify(self, simulation: SimulationResponse) -> SimulationResponse:
        working = SimulationResponse.model_validate(simulation.model_dump(mode="json"))
        fact_check = self._build_fact_check(working)
        citation_verification = self._build_citation_verification(working)
        audit_trail = self._build_audit_trail(working, fact_check, citation_verification)
        human_review = self._build_human_review_gate(working, fact_check, citation_verification)

        working.fact_check = fact_check
        working.citation_verification = citation_verification
        working.audit_trail = audit_trail
        working.human_review = human_review
        working.judge_summary.unsupported_claims = fact_check.unsupported_claims
        working.judge_summary.recommended_human_review = human_review.required
        working.final_report.human_review_checklist = dedupe(
            working.final_report.human_review_checklist + human_review.checklist
        )
        working.case.status = (
            CaseStatus.REVIEW_REQUIRED if human_review.required else CaseStatus.REPORT_READY
        )
        return working

    def _build_fact_check(self, simulation: SimulationResponse) -> FactCheckResult:
        evidence_ids = {item.evidence_id for item in simulation.case.evidence}
        citation_ids = {item.citation_id for item in simulation.case.citations}
        unsupported_claims = [
            claim.claim_id
            for claim in simulation.case.claims
            if not claim.evidence_ids or any(evidence_id not in evidence_ids for evidence_id in claim.evidence_ids)
        ]
        citation_mismatches = [
            claim.claim_id
            for claim in simulation.case.claims
            if any(citation_id not in citation_ids for citation_id in claim.citation_ids)
        ]
        contradictions: list[str] = []
        if any(item.status != "uncontested" for item in simulation.case.evidence):
            contradictions.append(
                "Một số chứng cứ vẫn ở trạng thái disputed nên cần đối chiếu thêm trước khi kết luận."
            )
        if any(
            evidence.challenged_by
            for evidence in simulation.case.evidence
            if evidence.used_by and evidence.challenged_by
        ):
            contradictions.append(
                "Có chứng cứ được cả hai bên viện dẫn nhưng đồng thời đang bị phản biện/challenged."
            )
        if any(
            claim.speaker.value == "defense_agent" and "thanh toán" in claim.content.lower()
            for claim in simulation.case.claims
        ):
            contradictions.append(
                "Lập luận của bị đơn cho thấy điều kiện thanh toán còn lại vẫn chưa được làm rõ hoàn toàn."
            )

        risk_level = ClaimConfidence.LOW
        if unsupported_claims or citation_mismatches:
            risk_level = ClaimConfidence.HIGH
        elif contradictions:
            risk_level = ClaimConfidence.MEDIUM
        return FactCheckResult(
            unsupported_claims=unsupported_claims,
            contradictions=contradictions,
            citation_mismatches=citation_mismatches,
            risk_level=risk_level,
        )

    def _build_citation_verification(self, simulation: SimulationResponse) -> CitationVerificationResult:
        accepted: list[str] = []
        rejected: list[str] = []
        warnings: list[str] = []
        for citation in simulation.case.citations:
            if citation.effective_status.value == "active":
                accepted.append(citation.citation_id)
            elif citation.effective_status.value == "expired":
                rejected.append(citation.citation_id)
                warnings.append(
                    f"Citation {citation.citation_id} ({citation.article}) đã hết hiệu lực hoặc cần thay thế."
                )
            else:
                warnings.append(
                    f"Citation {citation.citation_id} ({citation.article}) chưa xác định rõ trạng thái hiệu lực."
                )

        used_citation_ids = {
            citation_id
            for claim in simulation.case.claims
            for citation_id in claim.citation_ids
        }
        retrieved_citation_ids = {citation.citation_id for citation in simulation.case.citations}
        for citation_id in sorted(used_citation_ids - retrieved_citation_ids):
            rejected.append(citation_id)
            warnings.append(
                f"Citation {citation_id} được dùng trong claim nhưng không tồn tại trong retrieved set."
            )
        if simulation.case.citations:
            warnings.append("Cần đối chiếu citation với nguồn văn bản pháp luật chính thức trước khi human review.")
        return CitationVerificationResult(
            accepted_citations=dedupe(accepted),
            rejected_citations=dedupe(rejected),
            warnings=dedupe(warnings),
        )

    def _build_audit_trail(
        self,
        simulation: SimulationResponse,
        fact_check: FactCheckResult,
        citation_verification: CitationVerificationResult,
    ) -> list[AuditEvent]:
        events: list[AuditEvent] = [
            AuditEvent(
                event_id="AUDIT_001",
                stage=AuditStage.RETRIEVAL,
                severity=ClaimConfidence.LOW,
                message=f"Retrieved {len(simulation.case.citations)} citations for structured simulation.",
                related_citation_ids=[citation.citation_id for citation in simulation.case.citations],
            )
        ]
        if fact_check.unsupported_claims:
            events.append(
                AuditEvent(
                    event_id=f"AUDIT_{len(events) + 1:03d}",
                    stage=AuditStage.VERIFICATION,
                    severity=ClaimConfidence.HIGH,
                    message="Unsupported claims were detected because they do not have sufficient evidence grounding.",
                    related_claim_ids=fact_check.unsupported_claims,
                )
            )
        if fact_check.contradictions:
            events.append(
                AuditEvent(
                    event_id=f"AUDIT_{len(events) + 1:03d}",
                    stage=AuditStage.VERIFICATION,
                    severity=ClaimConfidence.MEDIUM,
                    message="Contradictions or unresolved disputed evidence require follow-up review.",
                    related_evidence_ids=[
                        evidence.evidence_id
                        for evidence in simulation.case.evidence
                        if evidence.status != "uncontested" or evidence.challenged_by
                    ],
                )
            )
        if citation_verification.rejected_citations:
            events.append(
                AuditEvent(
                    event_id=f"AUDIT_{len(events) + 1:03d}",
                    stage=AuditStage.VERIFICATION,
                    severity=ClaimConfidence.HIGH,
                    message="Some citations were rejected because they were not retrieved or are outdated.",
                    related_citation_ids=citation_verification.rejected_citations,
                )
            )
        if citation_verification.warnings:
            events.append(
                AuditEvent(
                    event_id=f"AUDIT_{len(events) + 1:03d}",
                    stage=AuditStage.JUDICIAL_REVIEW,
                    severity=ClaimConfidence.MEDIUM,
                    message="Verification generated legal-basis warnings that should be reviewed by a human.",
                    related_citation_ids=dedupe(
                        [citation.citation_id for citation in simulation.case.citations]
                    ),
                )
            )
        return events

    def _build_human_review_gate(
        self,
        simulation: SimulationResponse,
        fact_check: FactCheckResult,
        citation_verification: CitationVerificationResult,
    ) -> HumanReviewGate:
        reasons: list[str] = []
        checklist: list[str] = [
            "Đối chiếu lại các citation với nguồn văn bản pháp luật chính thức.",
            "Xác minh nguyên văn điều khoản hợp đồng và chứng cứ tệp đính kèm.",
        ]
        if fact_check.unsupported_claims:
            reasons.append("Có claim chưa được grounding đầy đủ bằng evidence.")
            checklist.append("Bổ sung hoặc loại bỏ các claim đang thiếu evidence support.")
        if fact_check.contradictions:
            reasons.append("Còn tồn tại mâu thuẫn hoặc disputed evidence trong hồ sơ.")
            checklist.append("Làm rõ các disputed evidence và contradiction trước khi chốt kết luận.")
        if citation_verification.rejected_citations:
            reasons.append("Có citation bị reject hoặc không nằm trong retrieved set.")
            checklist.append("Thay thế hoặc loại bỏ các citation bị reject.")
        if citation_verification.warnings:
            reasons.append("Có legal basis warning cần human review.")
        required = bool(reasons) or fact_check.risk_level != ClaimConfidence.LOW
        return HumanReviewGate(
            required=required,
            blocked=required,
            reasons=dedupe(reasons),
            checklist=dedupe(checklist),
        )


@lru_cache(maxsize=1)
def get_verification_service() -> VerificationService:
    return VerificationService()
