from __future__ import annotations

from functools import lru_cache
from html import escape

import markdown as markdown_lib

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
        accepted_citation_ids = set(citation_verification.accepted_citations)
        accepted_citations = [
            citation
            for citation in simulation.case.citations
            if citation.citation_id in accepted_citation_ids
        ]
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
            visible_citation_ids = [
                citation_id for citation_id in claim.citation_ids if citation_id in accepted_citation_ids
            ]
            lines.extend(
                [
                    f"### {claim.claim_id} - {claim.speaker.value}",
                    "",
                    claim.content,
                    "",
                    f"- Confidence: `{claim.confidence.value}`",
                    f"- Evidence: {', '.join(claim.evidence_ids) if claim.evidence_ids else 'None'}",
                    (
                        f"- Citations: {', '.join(visible_citation_ids)}"
                        if visible_citation_ids
                        else "- Citations: None kept after verification"
                    ),
                    "",
                ]
            )

        lines.extend(
            [
                "## Citations",
                "",
            ]
        )
        for citation in accepted_citations:
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
        if not accepted_citations:
            lines.extend(
                [
                    "- No accepted citations remained after verification.",
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


class HtmlReportService:
    def render(self, *, title: str, markdown_text: str) -> str:
        body = markdown_lib.markdown(
            markdown_text,
            extensions=[
                "extra",
                "fenced_code",
                "tables",
                "sane_lists",
                "nl2br",
            ],
        )
        safe_title = escape(title)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f1e8;
      --paper: #fffdf8;
      --ink: #1e1a17;
      --muted: #6e6257;
      --line: #d9cfc2;
      --accent: #8d2b1e;
      --accent-soft: #f2ddd8;
      --code: #f3eee6;
      --shadow: rgba(30, 26, 23, 0.12);
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top, #fff7ef 0%, transparent 38%),
        linear-gradient(180deg, #efe5d7 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    main {{
      max-width: 920px;
      margin: 32px auto;
      padding: 40px 48px;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 24px 60px var(--shadow);
    }}
    h1, h2, h3 {{
      line-height: 1.2;
      margin-top: 1.6em;
      margin-bottom: 0.6em;
    }}
    h1 {{
      margin-top: 0;
      font-size: 2rem;
      border-bottom: 3px solid var(--accent);
      padding-bottom: 0.4rem;
    }}
    h2 {{
      font-size: 1.35rem;
      color: var(--accent);
    }}
    h3 {{
      font-size: 1.05rem;
    }}
    p, li {{
      font-size: 1rem;
      line-height: 1.72;
    }}
    ul {{
      padding-left: 1.4rem;
    }}
    code {{
      font-family: Consolas, "Courier New", monospace;
      background: var(--code);
      padding: 0.1rem 0.35rem;
      border-radius: 6px;
    }}
    pre {{
      overflow-x: auto;
      padding: 1rem;
      border-radius: 12px;
      background: var(--code);
      border: 1px solid var(--line);
    }}
    blockquote {{
      margin: 1rem 0;
      padding: 0.2rem 1rem;
      border-left: 4px solid var(--accent);
      background: var(--accent-soft);
      color: var(--muted);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 0.7rem;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f8f2ea;
    }}
    hr {{
      border: 0;
      border-top: 1px solid var(--line);
      margin: 2rem 0;
    }}
    .report-meta {{
      color: var(--muted);
      font-size: 0.95rem;
      margin-bottom: 1.2rem;
    }}
    @media (max-width: 720px) {{
      main {{
        margin: 0;
        min-height: 100vh;
        border-radius: 0;
        padding: 24px 18px 36px;
      }}
      h1 {{
        font-size: 1.6rem;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="report-meta">AI Courtroom Harness HTML Preview</div>
    {body}
  </main>
</body>
</html>
"""


@lru_cache(maxsize=1)
def get_markdown_report_service() -> MarkdownReportService:
    return MarkdownReportService()


@lru_cache(maxsize=1)
def get_html_report_service() -> HtmlReportService:
    return HtmlReportService()
