from __future__ import annotations

from functools import lru_cache
from html import escape

import markdown as markdown_lib

from packages.shared.python.ai_court_shared.schemas import (
    AgentName,
    AgentTurn,
    HearingSession,
    HumanReviewRecord,
    SimulationResponse,
    V2TrialSession,
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
    metadata_items = [
        f"<li><strong>Mã lượt:</strong> <code>{escape(turn.turn_id)}</code></li>",
        f"<li><strong>Trạng thái:</strong> <code>{escape(turn.status.value)}</code></li>",
    ]
    if turn.claims:
        metadata_items.append(
            f"<li><strong>Yêu cầu liên quan:</strong> {escape(', '.join(turn.claims))}</li>"
        )
    if turn.evidence_used:
        metadata_items.append(
            f"<li><strong>Chứng cứ sử dụng:</strong> {escape(', '.join(turn.evidence_used))}</li>"
        )
    if visible_citations:
        metadata_items.append(
            f"<li><strong>Căn cứ pháp lý được giữ lại:</strong> {escape(', '.join(visible_citations))}</li>"
        )
    lines = [
        '<section class="transcript-turn">',
        '  <div class="transcript-turn-header">',
        f'    <span class="transcript-stage">{escape(hearing_stage_label(turn.agent))}</span>',
        f'    <h3>{escape(agent_label(turn.agent))}</h3>',
        "  </div>",
        f'  <ul class="transcript-meta">{"".join(metadata_items)}</ul>',
        f'  <div class="transcript-speech"><span class="transcript-speech-label">Nội dung ghi nhận</span><p>{escape(turn.message)}</p></div>',
        "</section>",
        "",
    ]
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


def render_v1_table(rows: list[tuple[str, str]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {key} | {value or 'None'} |")
    return lines


class V1HearingRecordService:
    def render(self, hearing: HearingSession) -> str:
        lines: list[str] = [
            f"# V1 Simulated Hearing Record - {hearing.case.case_id}",
            "",
            "> Non-binding courtroom simulation record for legal education and decision-support. This is not a judgment.",
            "",
            "## Case Metadata",
            "",
            *render_v1_table(
                [
                    ("Case ID", f"`{hearing.case.case_id}`"),
                    ("Session ID", f"`{hearing.session_id}`"),
                    ("Status", f"`{hearing.status.value}`"),
                    ("Current stage", f"`{hearing.current_stage.value}`"),
                    ("Case type", f"`{hearing.case.case_type.value}`"),
                ]
            ),
            "",
            "## Procedural Timeline",
            "",
        ]
        for index, stage in enumerate(hearing.stage_order, start=1):
            stage_turns = [turn for turn in hearing.turns if turn.hearing_stage == stage]
            marker = "completed" if stage_turns else "pending"
            lines.append(f"{index}. `{stage.value}` - {marker} - {len(stage_turns)} turn(s)")

        lines.extend(["", "## Evidence Registry", ""])
        if not hearing.case.evidence:
            lines.extend(["- No evidence captured.", ""])
        for evidence in hearing.case.evidence:
            lines.extend(
                [
                    f"### {evidence.evidence_id} - {evidence.type.value}",
                    "",
                    evidence.content,
                    "",
                    f"- Source: {evidence.source}",
                    f"- Status: `{evidence.status.value}`",
                    f"- Used by: {', '.join(evidence.used_by) if evidence.used_by else 'None'}",
                    f"- Challenged by: {', '.join(evidence.challenged_by) if evidence.challenged_by else 'None'}",
                    "",
                ]
            )

        lines.extend(["## Evidence Challenges", ""])
        if not hearing.evidence_challenges:
            lines.extend(["- No evidence challenges recorded.", ""])
        for challenge in hearing.evidence_challenges:
            lines.extend(
                [
                    f"### {challenge.challenge_id} - {challenge.evidence_id}",
                    "",
                    f"- Raised by: `{challenge.raised_by.value}`",
                    f"- Admissibility: `{challenge.admissibility.value}`",
                    f"- Affected claims: {', '.join(challenge.affected_claim_ids) if challenge.affected_claim_ids else 'None'}",
                    f"- Reason: {challenge.reason}",
                    f"- Resolution note: {challenge.resolution_notes or 'None'}",
                    "",
                ]
            )

        lines.extend(["## Party Arguments", ""])
        for claim in hearing.case.claims:
            lines.extend(
                [
                    f"### {claim.claim_id} - {agent_label(claim.speaker)}",
                    "",
                    claim.content,
                    "",
                    f"- Confidence: `{claim.confidence.value}`",
                    f"- Evidence: {', '.join(claim.evidence_ids) if claim.evidence_ids else 'None'}",
                    f"- Citations: {', '.join(claim.citation_ids) if claim.citation_ids else 'None'}",
                    "",
                ]
            )
        if not hearing.case.claims:
            lines.extend(["- No party claims recorded.", ""])

        lines.extend(["## Judge Clarification Questions And Responses", ""])
        for question in hearing.clarification_questions:
            lines.extend(
                [
                    f"### {question.question_id}",
                    "",
                    question.question,
                    "",
                    f"- Status: `{question.status.value}`",
                    f"- Related claims: {', '.join(question.related_claim_ids) if question.related_claim_ids else 'None'}",
                    f"- Related evidence: {', '.join(question.related_evidence_ids) if question.related_evidence_ids else 'None'}",
                    "",
                ]
            )
            responses = [response for response in hearing.party_responses if response.question_id == question.question_id]
            if not responses:
                lines.extend(["- No party responses recorded.", ""])
            for response in responses:
                lines.extend(
                    [
                        f"- `{response.responder.value}` `{response.status.value}`: {response.content}",
                        f"  - Evidence: {', '.join(response.evidence_ids) if response.evidence_ids else 'None'}",
                        f"  - Citations: {', '.join(response.citation_ids) if response.citation_ids else 'None'}",
                    ]
                )
            lines.append("")

        lines.extend(["## Verification Agents", ""])
        if hearing.fact_check is not None:
            lines.extend(
                [
                    "### Fact-check Agent",
                    "",
                    f"- Risk level: `{hearing.fact_check.risk_level.value}`",
                    "- Unsupported claims:",
                    *bullet_lines(hearing.fact_check.unsupported_claims),
                    "- Contradictions:",
                    *bullet_lines(hearing.fact_check.contradictions),
                    "- Citation mismatches:",
                    *bullet_lines(hearing.fact_check.citation_mismatches),
                    "",
                ]
            )
        if hearing.citation_verification is not None:
            lines.extend(
                [
                    "### Citation Verifier Agent",
                    "",
                    "- Accepted citations:",
                    *bullet_lines(hearing.citation_verification.accepted_citations),
                    "- Rejected citations:",
                    *bullet_lines(hearing.citation_verification.rejected_citations),
                    "- Warnings:",
                    *bullet_lines(hearing.citation_verification.warnings),
                    "",
                ]
            )

        lines.extend(["## Non-Binding Proposed Outcome", ""])
        if not hearing.outcome_candidates:
            lines.extend(["- No outcome candidate generated.", ""])
        for outcome in hearing.outcome_candidates:
            lines.extend(
                [
                    f"### {outcome.outcome_id} - `{outcome.disposition.value}`",
                    "",
                    outcome.rationale,
                    "",
                    f"- Risk level: `{outcome.risk_level.value}`",
                    f"- Requires human review: `{outcome.requires_human_review}`",
                    f"- Supported claims: {', '.join(outcome.supported_claim_ids) if outcome.supported_claim_ids else 'None'}",
                    f"- Evidence: {', '.join(outcome.evidence_ids) if outcome.evidence_ids else 'None'}",
                    f"- Citations: {', '.join(outcome.citation_ids) if outcome.citation_ids else 'None'}",
                    f"- Disclaimer: {outcome.disclaimer}",
                    "",
                ]
            )

        lines.extend(["## Human Review Gate", ""])
        lines.extend(
            [
                f"- Required: `{hearing.human_review.required}`",
                f"- Blocked: `{hearing.human_review.blocked}`",
                "",
                "### Reasons",
                "",
                *bullet_lines(hearing.human_review.reasons),
                "",
                "### Checklist",
                "",
                *bullet_lines(hearing.human_review.checklist),
                "",
            ]
        )

        lines.extend(["## Full Stage Transcript", ""])
        for turn in hearing.turns:
            lines.extend(
                [
                    f"### {turn.turn_id} - `{turn.hearing_stage.value}` - {agent_label(turn.agent)}",
                    "",
                    turn.message,
                    "",
                    f"- Status: `{turn.status.value}`",
                    f"- Claims: {', '.join(turn.claims) if turn.claims else 'None'}",
                    f"- Evidence: {', '.join(turn.evidence_used) if turn.evidence_used else 'None'}",
                    f"- Citations: {', '.join(turn.citations_used) if turn.citations_used else 'None'}",
                    f"- Tool calls: {', '.join(turn.tool_call_ids) if turn.tool_call_ids else 'None'}",
                    "",
                ]
            )

        lines.extend(["## Tool Call Trace", ""])
        if not hearing.tool_calls:
            lines.extend(["- No tool calls recorded.", ""])
        for tool_call in hearing.tool_calls:
            lines.extend(
                [
                    f"- `{tool_call.tool_call_id}` `{tool_call.tool_name}` by `{tool_call.agent.value}`: {tool_call.input_summary}",
                    f"  - Outputs: {', '.join(tool_call.output_refs) if tool_call.output_refs else 'None'}",
                    f"  - Status: `{tool_call.status.value}`",
                ]
            )

        lines.extend(["", "## Harness Violations", ""])
        if not hearing.harness_violations:
            lines.extend(["- No harness violations recorded.", ""])
        for violation in hearing.harness_violations:
            lines.extend(
                [
                    f"- `{violation.violation_id}` `{violation.rule}` `{violation.severity.value}`: {violation.message}",
                ]
            )

        lines.extend(
            [
                "",
                "## Disclaimer",
                "",
                "This V1 hearing record is a simulated, non-binding decision-support artifact. It is not legal advice, a court order, or an official judgment.",
                "",
            ]
        )
        return "\n".join(lines).strip() + "\n"


def render_v2_table(rows: list[tuple[str, str]]) -> list[str]:
    lines = ["| Mục | Nội dung |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {key} | {value or 'Không có'} |")
    return lines


class V2TrialRecordService:
    def render(self, trial: V2TrialSession) -> str:
        lines: list[str] = [
            f"# Biên Bản Phiên Tòa Mô Phỏng V2 - {trial.case.case_id}",
            "",
            "> Tài liệu mô phỏng không ràng buộc. Đây không phải bản án, quyết định của Tòa án hoặc tư vấn pháp lý.",
            "",
            "## Thông Tin Hồ Sơ",
            "",
            *render_v2_table(
                [
                    ("Mã hồ sơ", f"`{trial.case.case_id}`"),
                    ("Mã phiên", f"`{trial.session_id}`"),
                    ("Loại vụ việc", f"`{trial.case.case_type.value}`"),
                    ("Trạng thái", f"`{trial.status.value}`"),
                    ("Giai đoạn hiện tại", f"`{trial.current_stage.value}`"),
                    ("Human review mode", f"`{trial.human_review_mode.value}`"),
                ]
            ),
            "",
            "## Thành Phần Tham Gia",
            "",
        ]
        for appearance in trial.appearances:
            lines.extend(
                [
                    f"- `{appearance.appearance_id}` {appearance.display_name}: `{appearance.status.value}`"
                    + (f" ({appearance.notes})" if appearance.notes else ""),
                ]
            )
        if not trial.appearances:
            lines.append("- Chưa ghi nhận thành phần tham gia.")

        lines.extend(["", "## Trình Tự Thủ Tục", ""])
        for index, stage in enumerate(trial.stage_order, start=1):
            stage_turns = [turn for turn in trial.dialogue_turns if turn.trial_stage == stage]
            marker = "hoàn tất" if stage_turns else "chưa có lượt"
            lines.append(f"{index}. `{stage.value}` - {marker} - {len(stage_turns)} lượt")

        lines.extend(["", "## Hành Vi Tố Tụng Đã Ghi Nhận", ""])
        if not trial.procedural_acts:
            lines.append("- Không có hành vi tố tụng được ghi nhận.")
        for act in trial.procedural_acts:
            lines.extend(
                [
                    f"### {act.act_id} - {act.label}",
                    "",
                    act.content,
                    "",
                    f"- Giai đoạn: `{act.trial_stage.value}`",
                    f"- Người thực hiện: `{act.actor.value}`",
                    f"- Lượt liên quan: {', '.join(act.related_turn_ids) if act.related_turn_ids else 'Không có'}",
                    "",
                ]
            )

        lines.extend(["## Transcript Phiên Tòa", ""])
        for turn in trial.dialogue_turns:
            lines.extend(
                [
                    f"### {turn.turn_id} - `{turn.trial_stage.value}` - {turn.speaker_label}",
                    "",
                    turn.utterance,
                    "",
                    f"- Trạng thái: `{turn.status.value}`",
                    f"- Claim: {', '.join(turn.claim_ids) if turn.claim_ids else 'Không có'}",
                    f"- Chứng cứ: {', '.join(turn.evidence_ids) if turn.evidence_ids else 'Không có'}",
                    f"- Citation: {', '.join(turn.citation_ids) if turn.citation_ids else 'Không có'}",
                    f"- Risk notes: {', '.join(turn.risk_notes) if turn.risk_notes else 'Không có'}",
                    "",
                ]
            )

        lines.extend(["## Xét Chứng Cứ", ""])
        if not trial.evidence_examinations:
            lines.append("- Chưa có phần xét chứng cứ.")
        for exam in trial.evidence_examinations:
            lines.extend(
                [
                    f"### {exam.examination_id} - {exam.evidence_id}",
                    "",
                    f"- Bên giới thiệu: `{exam.introduced_by.value}`",
                    f"- Ý kiến nguyên đơn: {exam.plaintiff_position}",
                    f"- Ý kiến bị đơn: {exam.defense_position}",
                    f"- Trạng thái xem xét: `{exam.admissibility.value}`",
                    f"- Claim liên quan: {', '.join(exam.related_claim_ids) if exam.related_claim_ids else 'Không có'}",
                    f"- Ghi chú: {exam.notes or 'Không có'}",
                    "",
                ]
            )

        lines.extend(["## Tranh Luận Và Đối Đáp", ""])
        if not trial.debate_rounds:
            lines.append("- Chưa có vòng tranh luận.")
        for debate in trial.debate_rounds:
            lines.extend(
                [
                    f"### {debate.debate_id} - {debate.topic}",
                    "",
                    f"- Lượt nguyên đơn: {', '.join(debate.plaintiff_turn_ids) if debate.plaintiff_turn_ids else 'Không có'}",
                    f"- Lượt bị đơn: {', '.join(debate.defense_turn_ids) if debate.defense_turn_ids else 'Không có'}",
                    f"- Tóm tắt của thẩm phán: {debate.judge_summary}",
                    f"- Điểm chưa giải quyết: {', '.join(debate.unresolved_points) if debate.unresolved_points else 'Không có'}",
                    "",
                ]
            )

        lines.extend(["## Lời Sau Cùng", ""])
        for statement in trial.final_statements:
            lines.extend(
                [
                    f"### {statement.statement_id} - {agent_label(statement.speaker)}",
                    "",
                    statement.content,
                    "",
                    f"- Đề nghị: {statement.requested_outcome or 'Không có'}",
                    f"- Chứng cứ: {', '.join(statement.evidence_ids) if statement.evidence_ids else 'Không có'}",
                    f"- Citation: {', '.join(statement.citation_ids) if statement.citation_ids else 'Không có'}",
                    "",
                ]
            )
        if not trial.final_statements:
            lines.append("- Chưa có lời sau cùng.")

        lines.extend(["## Nghị Án Mô Phỏng", ""])
        if trial.deliberation is None:
            lines.append("- Chưa có bản ghi nghị án.")
        else:
            lines.extend(
                [
                    f"- Mã nghị án: `{trial.deliberation.deliberation_id}`",
                    f"- Risk level: `{trial.deliberation.risk_level.value}`",
                    "",
                    "### Sự Kiện Đã Được Xác Lập",
                    "",
                    *bullet_lines(trial.deliberation.established_facts),
                    "",
                    "### Sự Kiện Còn Tranh Chấp",
                    "",
                    *bullet_lines(trial.deliberation.disputed_facts),
                    "",
                    "### Lập Luận Pháp Lý",
                    "",
                    *bullet_lines(trial.deliberation.legal_reasoning),
                    "",
                ]
            )

        lines.extend(["## Kết Quả Mô Phỏng Không Ràng Buộc", ""])
        if trial.simulated_decision is None:
            lines.append("- Chưa có kết quả mô phỏng.")
        else:
            decision = trial.simulated_decision
            lines.extend(
                [
                    f"- Mã kết quả: `{decision.decision_id}`",
                    f"- Disposition: `{decision.disposition.value}`",
                    f"- Risk level: `{decision.risk_level.value}`",
                    f"- Requires human review: `{decision.requires_human_review}`",
                    "",
                    "### Tóm Tắt",
                    "",
                    decision.summary,
                    "",
                    "### Hướng Xử Lý / Bước Tiếp Theo",
                    "",
                    decision.relief_or_next_step,
                    "",
                    "### Rationale",
                    "",
                    *bullet_lines(decision.rationale),
                    "",
                    f"- Claim hỗ trợ: {', '.join(decision.supported_claim_ids) if decision.supported_claim_ids else 'Không có'}",
                    f"- Chứng cứ: {', '.join(decision.evidence_ids) if decision.evidence_ids else 'Không có'}",
                    f"- Citation: {', '.join(decision.citation_ids) if decision.citation_ids else 'Không có'}",
                    f"- Disclaimer: {decision.non_binding_disclaimer}",
                    "",
                ]
            )

        lines.extend(["## Decision Guard", ""])
        if trial.decision_guard is None:
            lines.append("- Chưa có guard result.")
        else:
            guard = trial.decision_guard
            lines.extend(
                [
                    f"- Guard ID: `{guard.guard_id}`",
                    f"- Allowed to emit: `{guard.allowed_to_emit}`",
                    f"- Recommended disposition: `{guard.recommended_disposition.value if guard.recommended_disposition else 'None'}`",
                    f"- Grounded claims: {', '.join(guard.grounded_claim_ids) if guard.grounded_claim_ids else 'Không có'}",
                    f"- Official language hits: {', '.join(guard.official_language_hits) if guard.official_language_hits else 'Không có'}",
                    "",
                    "### Unresolved Items",
                    "",
                    *bullet_lines(guard.unresolved_items),
                    "",
                    "### Warnings",
                    "",
                    *bullet_lines(guard.warnings),
                    "",
                ]
            )

        lines.extend(
            [
                "## Verification",
                "",
                f"- Fact-check risk: `{trial.fact_check.risk_level.value if trial.fact_check else 'not_run'}`",
                f"- Accepted citations: {', '.join(trial.citation_verification.accepted_citations) if trial.citation_verification else 'Không có'}",
                f"- Rejected citations: {', '.join(trial.citation_verification.rejected_citations) if trial.citation_verification else 'Không có'}",
                "",
                "## Dialogue Quality",
                "",
                f"- Max utterance chars: `{trial.dialogue_quality.max_utterance_chars}`",
                f"- Overlong turns: {', '.join(trial.dialogue_quality.overlong_turn_ids) if trial.dialogue_quality.overlong_turn_ids else 'Không có'}",
                f"- Ungrounded turns: {', '.join(trial.dialogue_quality.ungrounded_turn_ids) if trial.dialogue_quality.ungrounded_turn_ids else 'Không có'}",
                f"- Role drift warnings: {', '.join(trial.dialogue_quality.role_drift_warnings) if trial.dialogue_quality.role_drift_warnings else 'Không có'}",
                "",
                "## Human Review",
                "",
                f"- Required: `{trial.human_review.required}`",
                f"- Blocked: `{trial.human_review.blocked}`",
                "",
                "### Reasons",
                "",
                *bullet_lines(trial.human_review.reasons),
                "",
                "### Checklist",
                "",
                *bullet_lines(trial.human_review.checklist),
                "",
                "## Disclaimer",
                "",
                "Biên bản này là mô phỏng không ràng buộc cho mục đích học tập, demo và hỗ trợ phân tích. Không sử dụng như bản án, quyết định của Tòa án hoặc tư vấn pháp lý.",
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
    .transcript-turn {{
      margin: 1rem 0 1.35rem;
      padding: 1rem 1.1rem 1.15rem;
      border: 1px solid var(--line);
      background: #fbfbfa;
    }}
    .transcript-turn-header {{
      display: flex;
      align-items: baseline;
      gap: 0.7rem;
      margin-bottom: 0.7rem;
      padding-bottom: 0.55rem;
      border-bottom: 1px solid var(--line);
    }}
    .transcript-turn-header h3 {{
      margin: 0;
      font-size: 1.02rem;
    }}
    .transcript-stage {{
      display: inline-block;
      padding: 0.12rem 0.45rem;
      border: 1px solid var(--strong-line);
      font-size: 0.82rem;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      color: var(--muted);
      background: #f3f3f0;
      font-family: "Segoe UI", Arial, sans-serif;
    }}
    .transcript-meta {{
      margin: 0 0 0.75rem;
      padding-left: 1.15rem;
    }}
    .transcript-meta li {{
      margin-top: 0.15rem;
      line-height: 1.65;
    }}
    .transcript-speech {{
      padding: 0.85rem 0.95rem;
      border-left: 3px solid var(--strong-line);
      background: #ffffff;
    }}
    .transcript-speech-label {{
      display: block;
      margin-bottom: 0.45rem;
      font-size: 0.84rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--muted);
      font-family: "Segoe UI", Arial, sans-serif;
    }}
    .transcript-speech p {{
      margin: 0;
      text-align: left;
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
      .transcript-turn-header {{
        display: block;
      }}
      .transcript-stage {{
        margin-bottom: 0.45rem;
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


@lru_cache(maxsize=1)
def get_v1_hearing_record_service() -> V1HearingRecordService:
    return V1HearingRecordService()


@lru_cache(maxsize=1)
def get_v2_trial_record_service() -> V2TrialRecordService:
    return V2TrialRecordService()
