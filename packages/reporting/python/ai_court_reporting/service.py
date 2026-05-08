from __future__ import annotations

from functools import lru_cache

from packages.shared.python.ai_court_shared.schemas import (
    HumanReviewRecord,
    SimulationResponse,
)


def bullet_lines(values: list[str], fallback: str = "- None") -> list[str]:
    if not values:
        return [fallback]
    return [f"- {value}" for value in values]


class MarkdownReportService:
    def render(self, simulation: SimulationResponse, review_record: HumanReviewRecord | None) -> str:
        report = simulation.final_report
        judge = simulation.judge_summary
        fact_check = simulation.fact_check
        citation_verification = simulation.citation_verification
        lines: list[str] = [
            f"# AI Courtroom Harness Report - {simulation.case.case_id}",
            "",
            f"Status: `{simulation.case.status.value}`",
            "",
            "## Case Summary",
            "",
            report.case_summary,
            "",
            "## Disputed Points",
            "",
            *bullet_lines(report.disputed_points),
            "",
            "## Judge Summary",
            "",
            judge.summary,
            "",
            "## Questions To Clarify",
            "",
            *bullet_lines(judge.questions_to_clarify),
            "",
            "## Claims",
            "",
        ]
        for claim in simulation.case.claims:
            lines.extend(
                [
                    f"### {claim.claim_id} - {claim.speaker.value}",
                    "",
                    claim.content,
                    "",
                    f"- Confidence: `{claim.confidence.value}`",
                    f"- Evidence: {', '.join(claim.evidence_ids) if claim.evidence_ids else 'None'}",
                    f"- Citations: {', '.join(claim.citation_ids) if claim.citation_ids else 'None'}",
                    "",
                ]
            )

        lines.extend(
            [
                "## Citations",
                "",
            ]
        )
        for citation in simulation.case.citations:
            lines.extend(
                [
                    f"### {citation.citation_id} - {citation.article} - {citation.title}",
                    "",
                    citation.content,
                    "",
                    f"- Effective status: `{citation.effective_status.value}`",
                    f"- Source: {citation.source}",
                    "",
                ]
            )

        lines.extend(
            [
                "## Fact Check",
                "",
                f"- Risk level: `{fact_check.risk_level.value}`",
                "",
                "### Unsupported Claims",
                "",
                *bullet_lines(fact_check.unsupported_claims),
                "",
                "### Contradictions",
                "",
                *bullet_lines(fact_check.contradictions),
                "",
                "### Citation Mismatches",
                "",
                *bullet_lines(fact_check.citation_mismatches),
                "",
                "## Citation Verification",
                "",
                "### Accepted Citations",
                "",
                *bullet_lines(citation_verification.accepted_citations),
                "",
                "### Rejected Citations",
                "",
                *bullet_lines(citation_verification.rejected_citations),
                "",
                "### Warnings",
                "",
                *bullet_lines(citation_verification.warnings),
                "",
                "## Audit Trail",
                "",
            ]
        )
        for event in simulation.audit_trail:
            lines.extend(
                [
                    f"- `{event.event_id}` [{event.stage.value}] `{event.severity.value}`: {event.message}",
                ]
            )

        lines.extend(
            [
                "",
                "## Human Review",
                "",
                f"- Required: `{simulation.human_review.required}`",
                f"- Blocked: `{simulation.human_review.blocked}`",
                "",
                "### Reasons",
                "",
                *bullet_lines(simulation.human_review.reasons),
                "",
                "### Checklist",
                "",
                *bullet_lines(simulation.human_review.checklist),
                "",
            ]
        )

        if review_record is not None:
            lines.extend(
                [
                    "## Review Resolution",
                    "",
                    f"- Reviewer: {review_record.reviewer_name}",
                    f"- Decision: `{review_record.decision.value}`",
                    f"- Resolved at: {review_record.resolved_at}",
                    f"- Status after: `{review_record.status_after.value}`",
                    "",
                    "### Reviewer Notes",
                    "",
                    review_record.notes or "No reviewer notes provided.",
                    "",
                    "### Reviewer Checklist Updates",
                    "",
                    *bullet_lines(review_record.checklist_updates),
                    "",
                ]
            )

        lines.extend(
            [
                "## Trial Minutes",
                "",
                simulation.trial_minutes.minutes_markdown,
                "",
                "## Disclaimer",
                "",
                report.disclaimer,
                "",
            ]
        )
        return "\n".join(lines).strip() + "\n"


@lru_cache(maxsize=1)
def get_markdown_report_service() -> MarkdownReportService:
    return MarkdownReportService()
