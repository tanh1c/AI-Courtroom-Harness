from __future__ import annotations

from functools import lru_cache
from html import escape

import markdown as markdown_lib

from packages.shared.python.ai_court_shared.schemas import (
    AgentName,
    AgentTurn,
    HumanReviewRecord,
    SimulationResponse,
)


def bullet_lines(values: list[str], fallback: str = "- None") -> list[str]:
    if not values:
        return [fallback]
    return [f"- {value}" for value in values]


def agent_label(agent: AgentName) -> str:
    labels = {
        AgentName.LEGAL_RETRIEVAL_AGENT: "Bộ phận tra cứu pháp lý",
        AgentName.PLAINTIFF_AGENT: "Nguyên đơn trình bày",
        AgentName.PROSECUTOR_AGENT: "Kiểm sát viên trình bày",
        AgentName.DEFENSE_AGENT: "Bị đơn đối đáp",
        AgentName.JUDGE_AGENT: "Thẩm phán nhận định sơ bộ",
        AgentName.CLERK_AGENT: "Thư ký ghi nhận",
        AgentName.FACT_CHECK_AGENT: "Kiểm tra sự kiện",
        AgentName.CITATION_VERIFIER_AGENT: "Kiểm tra căn cứ pháp lý",
    }
    return labels.get(agent, agent.value)


def hearing_stage_label(agent: AgentName) -> str:
    labels = {
        AgentName.LEGAL_RETRIEVAL_AGENT: "Mở phiên",
        AgentName.PLAINTIFF_AGENT: "Tranh tụng",
        AgentName.PROSECUTOR_AGENT: "Tranh tụng",
        AgentName.DEFENSE_AGENT: "Tranh tụng",
        AgentName.JUDGE_AGENT: "Nhận định sơ bộ",
        AgentName.CLERK_AGENT: "Kết thúc phiên",
        AgentName.FACT_CHECK_AGENT: "Kiểm tra sau phiên",
        AgentName.CITATION_VERIFIER_AGENT: "Kiểm tra sau phiên",
    }
    return labels.get(agent, "Diễn biến phiên")


def render_turn_transcript_lines(
    turn: AgentTurn,
    *,
    accepted_citation_ids: set[str],
) -> list[str]:
    visible_citations = [citation_id for citation_id in turn.citations_used if citation_id in accepted_citation_ids]
    lines = [
        f"### {hearing_stage_label(turn.agent)} - {agent_label(turn.agent)}",
        "",
        f"- Turn ID: `{turn.turn_id}`",
        f"- Status: `{turn.status.value}`",
    ]
    if turn.claims:
        lines.append(f"- Related claims: {', '.join(turn.claims)}")
    if turn.evidence_used:
        lines.append(f"- Evidence used: {', '.join(turn.evidence_used)}")
    if visible_citations:
        lines.append(f"- Accepted citations used: {', '.join(visible_citations)}")
    lines.extend(
        [
            "",
            f"> {turn.message}",
            "",
        ]
    )
    return lines


def render_session_outcome_lines(
    simulation: SimulationResponse,
    review_record: HumanReviewRecord | None,
) -> list[str]:
    lines = [
        "## Session Outcome",
        "",
        f"- Report status: `{simulation.case.status.value}`",
        (
            f"- Human review decision: `{review_record.decision.value}` by {review_record.reviewer_name}"
            if review_record is not None
            else f"- Human review blocked: `{simulation.human_review.blocked}`"
        ),
        "- End state: the simulated hearing is closed for report export and review tracking.",
        "- Note: this MVP does not generate an automatic judicial verdict or legally binding judgment.",
        "",
    ]
    return lines


def render_hearing_timeline_lines(
    simulation: SimulationResponse,
    review_record: HumanReviewRecord | None,
) -> list[str]:
    lines = [
        "## Hearing Timeline",
        "",
        "- `Mở phiên`: hệ thống hoàn tất intake hồ sơ, parse nội dung, và tra cứu các căn cứ pháp lý liên quan.",
        "- `Tranh tụng`: nguyên đơn nêu yêu cầu, sau đó bị đơn đối đáp với các điểm tranh chấp chính.",
        "- `Nhận định sơ bộ`: thẩm phán tóm tắt disputed points và nêu các câu hỏi cần làm rõ thêm.",
        "- `Kết thúc phiên`: thư ký ghi nhận biên bản mô phỏng, sau đó hệ thống chạy verification và audit checks.",
    ]
    if review_record is not None:
        lines.append(
            f"- `Kết thúc phiên`: human review chấp thuận báo cáo với quyết định `{review_record.decision.value}`, đưa hồ sơ sang trạng thái `{review_record.status_after.value}`."
        )
    else:
        lines.append(
            f"- `Kết thúc phiên`: human review gate hiện có trạng thái required=`{simulation.human_review.required}`, blocked=`{simulation.human_review.blocked}`."
        )
    lines.extend(["", "## Courtroom Transcript", ""])
    return lines


def render_system_minutes_lines(minutes_markdown: str) -> list[str]:
    lines = [line for line in minutes_markdown.splitlines() if line.strip()]
    if lines and lines[0].startswith("## "):
        lines = lines[1:]
    return lines or ["- No system minutes captured."]


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
                *render_session_outcome_lines(simulation, review_record),
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
                *render_hearing_timeline_lines(simulation, review_record),
            ]
        )
        for turn in simulation.case.agent_turns:
            lines.extend(
                render_turn_transcript_lines(
                    turn,
                    accepted_citation_ids=accepted_citation_ids,
                )
            )

        lines.extend(
            [
                "## System Minutes",
                "",
                *render_system_minutes_lines(simulation.trial_minutes.minutes_markdown),
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
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --page: #f4f4f1;
      --paper: #ffffff;
      --ink: #171717;
      --muted: #5f5f5f;
      --line: #d7d7d2;
      --strong-line: #a8a8a1;
      --section: #242424;
      --code: #f7f7f5;
    }}
    * {{
      box-sizing: border-box;
    }}
    html {{
      font-size: 16px;
    }}
    body {{
      margin: 0;
      font-family: "Times New Roman", "Palatino Linotype", "Book Antiqua", "Noto Serif", "DejaVu Serif", serif;
      background: var(--page);
      color: var(--ink);
    }}
    .page {{
      max-width: 920px;
      margin: 0 auto;
      padding: 40px 24px 64px;
    }}
    main {{
      margin: 0 auto;
      padding: 44px 52px 56px;
      background: var(--paper);
      border: 1px solid var(--line);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
    }}
    h1, h2, h3 {{
      line-height: 1.3;
      margin-top: 1.8em;
      margin-bottom: 0.6em;
      font-weight: 700;
    }}
    h1 {{
      margin-top: 0;
      font-size: 2rem;
      padding-bottom: 0.65rem;
      border-bottom: 2px solid var(--strong-line);
      letter-spacing: 0.01em;
    }}
    h2 {{
      font-size: 1.2rem;
      color: var(--section);
      border-top: 1px solid var(--line);
      padding-top: 1rem;
    }}
    h3 {{
      font-size: 1rem;
    }}
    p, li {{
      font-size: 1rem;
      line-height: 1.8;
    }}
    p {{
      margin: 0.7rem 0;
      text-align: justify;
    }}
    ul {{
      margin: 0.4rem 0 1rem;
      padding-left: 1.3rem;
    }}
    li + li {{
      margin-top: 0.35rem;
    }}
    strong {{
      font-weight: 700;
    }}
    code {{
      font-family: Consolas, "Courier New", monospace;
      background: var(--code);
      border: 1px solid var(--line);
      padding: 0.08rem 0.32rem;
      border-radius: 3px;
      font-size: 0.94em;
    }}
    pre {{
      overflow-x: auto;
      padding: 1rem 1.1rem;
      background: var(--code);
      border: 1px solid var(--line);
    }}
    blockquote {{
      margin: 1rem 0;
      padding: 0.2rem 0 0.2rem 1rem;
      border-left: 3px solid var(--strong-line);
      color: var(--muted);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0 1.25rem;
      font-size: 0.96rem;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 0.7rem 0.75rem;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f5f5f2;
      font-weight: 700;
    }}
    hr {{
      border: 0;
      border-top: 1px solid var(--line);
      margin: 2rem 0;
    }}
    .report-meta {{
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 1.5rem;
      padding-bottom: 0.9rem;
      border-bottom: 1px solid var(--line);
      color: var(--muted);
      font-family: "Segoe UI", Arial, sans-serif;
      font-size: 0.88rem;
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }}
    .report-meta span:last-child {{
      text-align: right;
    }}
    .report-body {{
      word-break: normal;
      overflow-wrap: anywhere;
    }}
    @media print {{
      body {{
        background: #fff;
      }}
      .page {{
        padding: 0;
      }}
      main {{
        box-shadow: none;
        border: 0;
        padding: 0;
      }}
    }}
    @media (max-width: 720px) {{
      .page {{
        padding: 0;
      }}
      main {{
        margin: 0;
        min-height: 100vh;
        padding: 28px 20px 40px;
        box-shadow: none;
        border-left: 0;
        border-right: 0;
      }}
      h1 {{
        font-size: 1.55rem;
      }}
      .report-meta {{
        display: block;
      }}
      .report-meta span:last-child {{
        display: block;
        margin-top: 0.35rem;
        text-align: left;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <main>
      <div class="report-meta">
        <span>AI Courtroom Harness</span>
        <span>Formal Report Preview</span>
      </div>
      <div class="report-body">
        {body}
      </div>
    </main>
  </div>
</body>
</html>
"""


@lru_cache(maxsize=1)
def get_markdown_report_service() -> MarkdownReportService:
    return MarkdownReportService()


@lru_cache(maxsize=1)
def get_html_report_service() -> HtmlReportService:
    return HtmlReportService()
