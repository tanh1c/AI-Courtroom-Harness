from __future__ import annotations

from functools import lru_cache

from packages.retrieval.python.ai_court_retrieval.service import (
    get_local_legal_retrieval_service,
)
from packages.shared.python.ai_court_shared.schemas import (
    AgentName,
    AgentToolCall,
    AuditEvent,
    AuditStage,
    CaseState,
    CaseStatus,
    Citation,
    CitationVerificationResult,
    Claim,
    ClaimConfidence,
    ClarificationQuestion,
    EvidenceAdmissibility,
    EvidenceChallenge,
    EvidenceStatus,
    FactCheckResult,
    HarnessAction,
    HarnessViolation,
    HearingSession,
    HearingStage,
    HumanReviewGate,
    LegalSearchFilter,
    LegalSearchRequest,
    OutcomeCandidate,
    OutcomeDisposition,
    PartyResponse,
    TurnStatus,
    V1AgentTurn,
)


V1_STAGE_ORDER = [
    HearingStage.OPENING,
    HearingStage.EVIDENCE_PRESENTATION,
    HearingStage.LEGAL_RETRIEVAL,
    HearingStage.PLAINTIFF_ARGUMENT,
    HearingStage.DEFENSE_ARGUMENT,
    HearingStage.EVIDENCE_CHALLENGE,
    HearingStage.JUDGE_QUESTIONS,
    HearingStage.PARTY_RESPONSES,
    HearingStage.FACT_CHECK,
    HearingStage.CITATION_VERIFICATION,
    HearingStage.PRELIMINARY_ASSESSMENT,
    HearingStage.HUMAN_REVIEW,
    HearingStage.CLOSING_RECORD,
]


class HearingRuntimeError(ValueError):
    pass


def clone_case(case_state: CaseState) -> CaseState:
    return CaseState.model_validate(case_state.model_dump(mode="json"))


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def has_grounding(evidence_ids: list[str], citation_ids: list[str], content: str) -> bool:
    lowered = content.lower()
    explicitly_missing = "chưa có chứng cứ" in lowered or "chưa có citation" in lowered
    return bool(evidence_ids or citation_ids or explicitly_missing)


OFFICIAL_JUDGMENT_MARKERS = [
    "tòa tuyên",
    "tòa án tuyên",
    "tòa quyết định",
    "buộc bị đơn",
    "buộc nguyên đơn",
    "court orders",
    "the court hereby decides",
    "the court orders",
]

OUTCOME_DISCLAIMER = (
    "Non-binding proposed outcome for legal education and decision-support only; "
    "it is not a judgment, order, or substitute for qualified legal review."
)


def contains_official_judgment_language(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in OFFICIAL_JUDGMENT_MARKERS)


class CourtroomV1RuntimeService:
    def __init__(self) -> None:
        self.retrieval_service = get_local_legal_retrieval_service()

    def start(self, case_state: CaseState) -> HearingSession:
        case = clone_case(case_state)
        case.status = CaseStatus.SIMULATED
        session = HearingSession(
            session_id=f"HEARING_{case.case_id}",
            case=case,
            current_stage=HearingStage.OPENING,
            stage_order=V1_STAGE_ORDER,
            turns=[],
            audit_trail=[],
            human_review=HumanReviewGate(required=True, blocked=True),
            status=CaseStatus.SIMULATED,
        )
        self._append_turn(
            session,
            hearing_stage=HearingStage.OPENING,
            agent=AgentName.CLERK_AGENT,
            message=(
                "Thư ký mở phiên mô phỏng, ghi nhận hồ sơ đã được parse và chuyển sang "
                "quy trình V1 theo từng giai đoạn."
            ),
        )
        self._append_audit(
            session,
            stage=AuditStage.REPORTING,
            severity=ClaimConfidence.LOW,
            message="Started V1 stage-based hearing session.",
        )
        return session

    def advance(
        self,
        session: HearingSession,
        expected_stage: HearingStage | None = None,
    ) -> HearingSession:
        next_stage = self._next_stage(session)
        if expected_stage is not None and expected_stage != next_stage:
            raise HearingRuntimeError(
                f"Invalid stage transition: expected {expected_stage.value}, next is {next_stage.value}."
            )

        handlers = {
            HearingStage.EVIDENCE_PRESENTATION: self._advance_evidence_presentation,
            HearingStage.LEGAL_RETRIEVAL: self._advance_legal_retrieval,
            HearingStage.PLAINTIFF_ARGUMENT: self._advance_plaintiff_argument,
            HearingStage.DEFENSE_ARGUMENT: self._advance_defense_argument,
            HearingStage.EVIDENCE_CHALLENGE: self._advance_evidence_challenge,
            HearingStage.JUDGE_QUESTIONS: self._advance_judge_questions,
            HearingStage.PARTY_RESPONSES: self._advance_party_responses,
            HearingStage.FACT_CHECK: self._advance_fact_check,
            HearingStage.CITATION_VERIFICATION: self._advance_citation_verification,
            HearingStage.PRELIMINARY_ASSESSMENT: self._advance_preliminary_assessment,
            HearingStage.HUMAN_REVIEW: self._advance_human_review,
            HearingStage.CLOSING_RECORD: self._advance_closing_record,
        }
        handlers[next_stage](session)
        session.current_stage = next_stage
        return session

    def run_all(self, case_state: CaseState) -> HearingSession:
        session = self.start(case_state)
        while session.current_stage != HearingStage.CLOSING_RECORD:
            session = self.advance(session)
        return session

    def _next_stage(self, session: HearingSession) -> HearingStage:
        try:
            current_index = session.stage_order.index(session.current_stage)
        except ValueError as exc:
            raise HearingRuntimeError(f"Unknown current stage: {session.current_stage.value}") from exc
        next_index = current_index + 1
        if next_index >= len(session.stage_order):
            raise HearingRuntimeError("Hearing session is already at the final stage.")
        return session.stage_order[next_index]

    def _next_turn_id(self, session: HearingSession) -> str:
        return f"TURN_{len(session.turns) + 1:03d}"

    def _next_tool_call_id(self, session: HearingSession) -> str:
        return f"TOOL_{len(session.tool_calls) + 1:03d}"

    def _next_audit_id(self, session: HearingSession) -> str:
        return f"AUDIT_{len(session.audit_trail) + 1:03d}"

    def _append_turn(
        self,
        session: HearingSession,
        *,
        hearing_stage: HearingStage,
        agent: AgentName,
        message: str,
        claims: list[str] | None = None,
        evidence_used: list[str] | None = None,
        citations_used: list[str] | None = None,
        status: TurnStatus = TurnStatus.OK,
        tool_call_ids: list[str] | None = None,
    ) -> V1AgentTurn:
        turn = V1AgentTurn(
            turn_id=self._next_turn_id(session),
            agent=agent,
            message=message,
            claims=claims or [],
            evidence_used=evidence_used or [],
            citations_used=citations_used or [],
            status=status,
            hearing_stage=hearing_stage,
            tool_call_ids=tool_call_ids or [],
        )
        session.turns.append(turn)
        return turn

    def _append_audit(
        self,
        session: HearingSession,
        *,
        stage: AuditStage,
        severity: ClaimConfidence,
        message: str,
        related_claim_ids: list[str] | None = None,
        related_citation_ids: list[str] | None = None,
        related_evidence_ids: list[str] | None = None,
    ) -> None:
        session.audit_trail.append(
            AuditEvent(
                event_id=self._next_audit_id(session),
                stage=stage,
                severity=severity,
                message=message,
                related_claim_ids=related_claim_ids or [],
                related_citation_ids=related_citation_ids or [],
                related_evidence_ids=related_evidence_ids or [],
            )
        )

    def _next_violation_id(self, session: HearingSession) -> str:
        return f"VIOL_{len(session.harness_violations) + 1:03d}"

    def _advance_evidence_presentation(self, session: HearingSession) -> None:
        evidence_ids = [item.evidence_id for item in session.case.evidence]
        disputed_ids = [
            item.evidence_id for item in session.case.evidence if item.status != EvidenceStatus.UNCONTESTED
        ]
        turn_id = self._next_turn_id(session)
        tool_call = AgentToolCall(
            tool_call_id=self._next_tool_call_id(session),
            turn_id=turn_id,
            agent=AgentName.EVIDENCE_AGENT,
            tool_name="evidence_registry",
            input_summary=f"Inspect {len(evidence_ids)} evidence items and flag disputed records.",
            output_refs=evidence_ids,
        )
        session.tool_calls.append(tool_call)
        self._append_turn(
            session,
            hearing_stage=HearingStage.EVIDENCE_PRESENTATION,
            agent=AgentName.EVIDENCE_AGENT,
            message=(
                f"Evidence Agent trình bày {len(evidence_ids)} chứng cứ đã được trích xuất "
                f"và đánh dấu {len(disputed_ids)} mục cần theo dõi/challenge."
            ),
            evidence_used=evidence_ids,
            status=TurnStatus.NEEDS_REVIEW if disputed_ids else TurnStatus.OK,
            tool_call_ids=[tool_call.tool_call_id],
        )
        if disputed_ids:
            self._append_audit(
                session,
                stage=AuditStage.VERIFICATION,
                severity=ClaimConfidence.MEDIUM,
                message="Evidence Agent flagged disputed evidence for the V1 challenge flow.",
                related_evidence_ids=disputed_ids,
            )
        else:
            self._append_audit(
                session,
                stage=AuditStage.VERIFICATION,
                severity=ClaimConfidence.LOW,
                message="Evidence Agent found no disputed evidence at presentation stage.",
                related_evidence_ids=evidence_ids,
            )

    def _advance_legal_retrieval(self, session: HearingSession) -> None:
        retrieved: list[Citation] = []
        for issue in session.case.legal_issues:
            response = self.retrieval_service.search(
                LegalSearchRequest(
                    query=f"{issue.title}. {issue.description}",
                    top_k=2,
                    filters=LegalSearchFilter(),
                )
            )
            for citation in response.citations:
                if citation.citation_id not in {item.citation_id for item in retrieved}:
                    retrieved.append(citation)

        session.case.citations = retrieved
        tool_call = AgentToolCall(
            tool_call_id=self._next_tool_call_id(session),
            turn_id=self._next_turn_id(session),
            agent=AgentName.LEGAL_RETRIEVAL_AGENT,
            tool_name="legal_search",
            input_summary=f"Retrieve legal basis for {len(session.case.legal_issues)} issues.",
            output_refs=[citation.citation_id for citation in retrieved],
        )
        session.tool_calls.append(tool_call)
        self._append_turn(
            session,
            hearing_stage=HearingStage.LEGAL_RETRIEVAL,
            agent=AgentName.LEGAL_RETRIEVAL_AGENT,
            message=f"Legal Retrieval Agent thu thập {len(retrieved)} căn cứ pháp lý ứng viên.",
            citations_used=[citation.citation_id for citation in retrieved],
            tool_call_ids=[tool_call.tool_call_id],
        )
        self._append_audit(
            session,
            stage=AuditStage.RETRIEVAL,
            severity=ClaimConfidence.LOW,
            message="V1 hearing retrieved legal citations for procedural runtime.",
            related_citation_ids=[citation.citation_id for citation in retrieved],
        )

    def _advance_plaintiff_argument(self, session: HearingSession) -> None:
        evidence_ids = [item.evidence_id for item in session.case.evidence[:2]]
        citation_ids = [item.citation_id for item in session.case.citations[:2]]
        claim = Claim(
            claim_id=f"CLAIM_{len(session.case.claims) + 1:03d}",
            speaker=AgentName.PLAINTIFF_AGENT,
            content="Nguyên đơn cho rằng bên bán vi phạm nghĩa vụ giao tài sản đúng thời hạn.",
            evidence_ids=evidence_ids,
            citation_ids=citation_ids,
            confidence=ClaimConfidence.HIGH if evidence_ids and citation_ids else ClaimConfidence.MEDIUM,
        )
        session.case.claims.append(claim)
        self._append_turn(
            session,
            hearing_stage=HearingStage.PLAINTIFF_ARGUMENT,
            agent=AgentName.PLAINTIFF_AGENT,
            message=(
                "Nguyên đơn trình bày yêu cầu bảo vệ quyền lợi dựa trên hợp đồng, "
                "khoản thanh toán đã thực hiện và nghĩa vụ giao tài sản đúng hạn."
            ),
            claims=[claim.claim_id],
            evidence_used=evidence_ids,
            citations_used=citation_ids,
        )

    def _advance_defense_argument(self, session: HearingSession) -> None:
        evidence_ids = [item.evidence_id for item in session.case.evidence[:1]]
        citation_ids = [item.citation_id for item in session.case.citations[-2:]]
        claim = Claim(
            claim_id=f"CLAIM_{len(session.case.claims) + 1:03d}",
            speaker=AgentName.DEFENSE_AGENT,
            content="Bị đơn yêu cầu làm rõ điều kiện thanh toán còn lại trước khi kết luận vi phạm.",
            evidence_ids=evidence_ids,
            citation_ids=citation_ids,
            confidence=ClaimConfidence.MEDIUM,
        )
        session.case.claims.append(claim)
        self._append_turn(
            session,
            hearing_stage=HearingStage.DEFENSE_ARGUMENT,
            agent=AgentName.DEFENSE_AGENT,
            message=(
                "Bị đơn đối đáp rằng cần kiểm tra điều khoản thanh toán 30% còn lại "
                "và giá trị chứng minh của chứng cứ hợp đồng."
            ),
            claims=[claim.claim_id],
            evidence_used=evidence_ids,
            citations_used=citation_ids,
            status=TurnStatus.NEEDS_FACT_CHECK,
        )

    def _advance_evidence_challenge(self, session: HearingSession) -> None:
        disputed = [item for item in session.case.evidence if item.status.value != "uncontested"]
        if not disputed and session.case.evidence:
            disputed = [session.case.evidence[0]]
        for evidence in disputed[:2]:
            if AgentName.DEFENSE_AGENT.value not in evidence.challenged_by:
                evidence.challenged_by.append(AgentName.DEFENSE_AGENT.value)
            if evidence.status == EvidenceStatus.UNCONTESTED:
                evidence.status = EvidenceStatus.DISPUTED
            challenge = EvidenceChallenge(
                challenge_id=f"CHAL_{len(session.evidence_challenges) + 1:03d}",
                evidence_id=evidence.evidence_id,
                raised_by=AgentName.DEFENSE_AGENT,
                reason="Bị đơn yêu cầu đối chiếu nguyên văn và bối cảnh của chứng cứ này.",
                admissibility=EvidenceAdmissibility.NEEDS_REVIEW,
                affected_claim_ids=[claim.claim_id for claim in session.case.claims if evidence.evidence_id in claim.evidence_ids],
                resolved_by=AgentName.JUDGE_AGENT,
                resolution_notes="Chuyển sang human review trước khi dùng làm căn cứ kết luận.",
            )
            session.evidence_challenges.append(challenge)
        turn_id = self._next_turn_id(session)
        tool_call = AgentToolCall(
            tool_call_id=self._next_tool_call_id(session),
            turn_id=turn_id,
            agent=AgentName.EVIDENCE_AGENT,
            tool_name="evidence_challenge_registry",
            input_summary=f"Register {len(session.evidence_challenges)} evidence challenges.",
            output_refs=[challenge.challenge_id for challenge in session.evidence_challenges],
        )
        session.tool_calls.append(tool_call)
        self._append_turn(
            session,
            hearing_stage=HearingStage.EVIDENCE_CHALLENGE,
            agent=AgentName.EVIDENCE_AGENT,
            message=f"Evidence Agent ghi nhận {len(session.evidence_challenges)} challenge chứng cứ cần review.",
            evidence_used=[challenge.evidence_id for challenge in session.evidence_challenges],
            claims=dedupe(
                [
                    claim_id
                    for challenge in session.evidence_challenges
                    for claim_id in challenge.affected_claim_ids
                ]
            ),
            status=TurnStatus.NEEDS_REVIEW if session.evidence_challenges else TurnStatus.OK,
            tool_call_ids=[tool_call.tool_call_id],
        )
        if session.evidence_challenges:
            self._append_audit(
                session,
                stage=AuditStage.VERIFICATION,
                severity=ClaimConfidence.MEDIUM,
                message="Evidence challenges were persisted and linked to affected claims.",
                related_claim_ids=dedupe(
                    [
                        claim_id
                        for challenge in session.evidence_challenges
                        for claim_id in challenge.affected_claim_ids
                    ]
                ),
                related_evidence_ids=[challenge.evidence_id for challenge in session.evidence_challenges],
            )

    def _advance_judge_questions(self, session: HearingSession) -> None:
        questions = [
            ClarificationQuestion(
                question_id=f"QUES_{len(session.clarification_questions) + 1:03d}",
                asked_by=AgentName.JUDGE_AGENT,
                question="Hợp đồng quy định thời điểm thanh toán 30% còn lại trước hay sau khi giao tài sản?",
                target_agents=[AgentName.PLAINTIFF_AGENT, AgentName.DEFENSE_AGENT],
                related_claim_ids=[claim.claim_id for claim in session.case.claims],
                related_evidence_ids=[item.evidence_id for item in session.case.evidence[:1]],
                related_citation_ids=[item.citation_id for item in session.case.citations[:2]],
                status=TurnStatus.NEEDS_REVIEW,
            )
        ]
        if session.evidence_challenges:
            challenged_evidence_ids = dedupe(
                [challenge.evidence_id for challenge in session.evidence_challenges]
            )
            affected_claim_ids = dedupe(
                [
                    claim_id
                    for challenge in session.evidence_challenges
                    for claim_id in challenge.affected_claim_ids
                ]
            )
            questions.append(
                ClarificationQuestion(
                    question_id=f"QUES_{len(session.clarification_questions) + len(questions) + 1:03d}",
                    asked_by=AgentName.JUDGE_AGENT,
                    question=(
                        "Các chứng cứ đang bị challenge có đủ xác thực để hỗ trợ claim liên quan hay "
                        "cần loại khỏi phần nhận định sơ bộ?"
                    ),
                    target_agents=[AgentName.PLAINTIFF_AGENT, AgentName.DEFENSE_AGENT],
                    related_claim_ids=affected_claim_ids,
                    related_evidence_ids=challenged_evidence_ids,
                    related_citation_ids=[],
                    status=TurnStatus.NEEDS_REVIEW,
                )
            )
        if len(questions) < 2:
            questions.append(
                ClarificationQuestion(
                    question_id=f"QUES_{len(session.clarification_questions) + len(questions) + 1:03d}",
                    asked_by=AgentName.JUDGE_AGENT,
                    question="Thiệt hại phát sinh và yêu cầu hoàn trả tiền đã có chứng cứ trực tiếp nào ngoài narrative hay chưa?",
                    target_agents=[AgentName.PLAINTIFF_AGENT, AgentName.DEFENSE_AGENT],
                    related_claim_ids=[claim.claim_id for claim in session.case.claims],
                    related_evidence_ids=[item.evidence_id for item in session.case.evidence],
                    related_citation_ids=[item.citation_id for item in session.case.citations[:1]],
                    status=TurnStatus.NEEDS_REVIEW,
                )
            )
        session.clarification_questions.extend(questions)
        turn_id = self._next_turn_id(session)
        tool_call = AgentToolCall(
            tool_call_id=self._next_tool_call_id(session),
            turn_id=turn_id,
            agent=AgentName.JUDGE_AGENT,
            tool_name="clarification_question_planner",
            input_summary=(
                f"Generate targeted questions for {len(session.case.claims)} claims, "
                f"{len(session.evidence_challenges)} challenges, and {len(session.case.citations)} citations."
            ),
            output_refs=[question.question_id for question in questions],
            status=TurnStatus.NEEDS_REVIEW,
        )
        session.tool_calls.append(tool_call)
        self._append_turn(
            session,
            hearing_stage=HearingStage.JUDGE_QUESTIONS,
            agent=AgentName.JUDGE_AGENT,
            message=f"Thẩm phán đặt {len(questions)} câu hỏi làm rõ về điều kiện thanh toán, chứng cứ và claim còn tranh chấp.",
            claims=dedupe([claim_id for question in questions for claim_id in question.related_claim_ids]),
            evidence_used=dedupe([evidence_id for question in questions for evidence_id in question.related_evidence_ids]),
            citations_used=dedupe([citation_id for question in questions for citation_id in question.related_citation_ids]),
            status=TurnStatus.NEEDS_REVIEW,
            tool_call_ids=[tool_call.tool_call_id],
        )
        self._append_audit(
            session,
            stage=AuditStage.JUDICIAL_REVIEW,
            severity=ClaimConfidence.MEDIUM if session.evidence_challenges else ClaimConfidence.LOW,
            message=f"Judge issued {len(questions)} clarification questions.",
            related_claim_ids=dedupe([claim_id for question in questions for claim_id in question.related_claim_ids]),
            related_evidence_ids=dedupe([evidence_id for question in questions for evidence_id in question.related_evidence_ids]),
        )

    def _advance_party_responses(self, session: HearingSession) -> None:
        responses: list[PartyResponse] = []
        for question in session.clarification_questions:
            plaintiff_evidence = question.related_evidence_ids[:1]
            plaintiff_citations = question.related_citation_ids[:1]
            if plaintiff_evidence or plaintiff_citations:
                plaintiff_content = (
                    "Nguyên đơn trả lời dựa trên "
                    f"evidence {', '.join(plaintiff_evidence) or 'chưa có chứng cứ trực tiếp'} "
                    f"và citation {', '.join(plaintiff_citations) or 'chưa có citation bổ sung'}; "
                    "đề nghị giữ claim để human review đối chiếu nguyên văn."
                )
            else:
                plaintiff_content = "Nguyên đơn chưa có chứng cứ trực tiếp bổ sung cho câu hỏi này và đề nghị human review xác minh."
            plaintiff_status = (
                TurnStatus.OK
                if has_grounding(plaintiff_evidence, plaintiff_citations, plaintiff_content)
                and plaintiff_evidence
                else TurnStatus.NEEDS_FACT_CHECK
            )
            responses.append(
                PartyResponse(
                    response_id=f"RESP_{len(session.party_responses) + len(responses) + 1:03d}",
                    question_id=question.question_id,
                    responder=AgentName.PLAINTIFF_AGENT,
                    content=plaintiff_content,
                    evidence_ids=plaintiff_evidence,
                    citation_ids=plaintiff_citations,
                    status=plaintiff_status,
                )
            )

            defense_evidence = question.related_evidence_ids[:1]
            defense_content = (
                "Bị đơn phản hồi dựa trên "
                f"evidence {', '.join(defense_evidence) or 'chưa có chứng cứ trực tiếp'}; "
                "chưa có citation bổ sung nên đề nghị giữ câu hỏi ở trạng thái cần fact-check."
            )
            responses.append(
                PartyResponse(
                    response_id=f"RESP_{len(session.party_responses) + len(responses) + 1:03d}",
                    question_id=question.question_id,
                    responder=AgentName.DEFENSE_AGENT,
                    content=defense_content,
                    evidence_ids=defense_evidence,
                    citation_ids=[],
                    status=TurnStatus.NEEDS_FACT_CHECK,
                )
            )

        for question in session.clarification_questions:
            question_responses = [
                response for response in responses if response.question_id == question.question_id
            ]
            responders = {response.responder for response in question_responses}
            all_targets_answered = all(target in responders for target in question.target_agents)
            all_grounded = all(
                has_grounding(response.evidence_ids, response.citation_ids, response.content)
                and response.status == TurnStatus.OK
                for response in question_responses
            )
            question.status = TurnStatus.OK if all_targets_answered and all_grounded else TurnStatus.NEEDS_REVIEW

        session.party_responses.extend(responses)
        self._append_turn(
            session,
            hearing_stage=HearingStage.PARTY_RESPONSES,
            agent=AgentName.CLERK_AGENT,
            message=(
                f"Thư ký ghi nhận {len(responses)} phản hồi của nguyên đơn và bị đơn; "
                "các phản hồi thiếu evidence/citation rõ ràng được chuyển fact-check."
            ),
            evidence_used=dedupe([item for response in responses for item in response.evidence_ids]),
            citations_used=dedupe([item for response in responses for item in response.citation_ids]),
            status=TurnStatus.NEEDS_FACT_CHECK if any(response.status != TurnStatus.OK for response in responses) else TurnStatus.OK,
        )
        unresolved = [
            question for question in session.clarification_questions if question.status != TurnStatus.OK
        ]
        self._append_audit(
            session,
            stage=AuditStage.JUDICIAL_REVIEW,
            severity=ClaimConfidence.MEDIUM if unresolved else ClaimConfidence.LOW,
            message=f"Party responses left {len(unresolved)} clarification questions unresolved.",
            related_claim_ids=dedupe([claim_id for question in unresolved for claim_id in question.related_claim_ids]),
            related_evidence_ids=dedupe([evidence_id for question in unresolved for evidence_id in question.related_evidence_ids]),
        )

    def _advance_fact_check(self, session: HearingSession) -> None:
        citation_ids = {citation.citation_id for citation in session.case.citations}
        unsupported = [
            claim.claim_id
            for claim in session.case.claims
            if not claim.evidence_ids and not claim.citation_ids
        ]
        citation_mismatches = [
            claim.claim_id
            for claim in session.case.claims
            if any(citation_id not in citation_ids for citation_id in claim.citation_ids)
        ]
        contradictions = []
        if session.evidence_challenges:
            contradictions.append("Có chứng cứ đang bị challenge và cần human review.")
        if any(response.status == TurnStatus.NEEDS_FACT_CHECK for response in session.party_responses):
            contradictions.append("Có phản hồi của bên tham gia cần fact-check thêm.")
        unresolved_questions = [
            question for question in session.clarification_questions if question.status != TurnStatus.OK
        ]
        if unresolved_questions:
            contradictions.append(
                f"Còn {len(unresolved_questions)} câu hỏi làm rõ chưa được giải quyết đủ bằng evidence/citation."
            )
        risk = ClaimConfidence.HIGH if unsupported or citation_mismatches else ClaimConfidence.MEDIUM if contradictions else ClaimConfidence.LOW
        session.fact_check = FactCheckResult(
            unsupported_claims=unsupported,
            contradictions=contradictions,
            citation_mismatches=citation_mismatches,
            risk_level=risk,
        )
        turn_id = self._next_turn_id(session)
        tool_call = AgentToolCall(
            tool_call_id=self._next_tool_call_id(session),
            turn_id=turn_id,
            agent=AgentName.FACT_CHECK_AGENT,
            tool_name="claim_support_check",
            input_summary=f"Check {len(session.case.claims)} claims against evidence and citations.",
            output_refs=dedupe(unsupported + citation_mismatches),
            status=TurnStatus.NEEDS_REVIEW if risk != ClaimConfidence.LOW else TurnStatus.OK,
        )
        session.tool_calls.append(tool_call)
        self._append_turn(
            session,
            hearing_stage=HearingStage.FACT_CHECK,
            agent=AgentName.FACT_CHECK_AGENT,
            message=(
                f"Fact-check Agent kiểm tra {len(session.case.claims)} claim, "
                f"phát hiện {len(unsupported)} claim thiếu support và {len(citation_mismatches)} citation mismatch."
            ),
            claims=dedupe(unsupported + citation_mismatches),
            evidence_used=[challenge.evidence_id for challenge in session.evidence_challenges],
            status=TurnStatus.NEEDS_REVIEW if risk != ClaimConfidence.LOW else TurnStatus.OK,
            tool_call_ids=[tool_call.tool_call_id],
        )
        self._append_audit(
            session,
            stage=AuditStage.VERIFICATION,
            severity=risk,
            message=f"Fact-check Agent completed with risk level {risk.value}.",
            related_claim_ids=dedupe(unsupported + citation_mismatches),
            related_evidence_ids=[challenge.evidence_id for challenge in session.evidence_challenges],
        )

    def _advance_citation_verification(self, session: HearingSession) -> None:
        accepted = [citation.citation_id for citation in session.case.citations if citation.effective_status.value == "active"]
        rejected = [citation.citation_id for citation in session.case.citations if citation.effective_status.value == "expired"]
        unknown = [citation.citation_id for citation in session.case.citations if citation.effective_status.value == "unknown"]
        session.citation_verification = CitationVerificationResult(
            accepted_citations=accepted,
            rejected_citations=rejected,
            warnings=dedupe(
                ["Cần đối chiếu citation với nguồn văn bản chính thức trước khi xuất báo cáo V1."]
                + (["Có citation chưa xác định rõ trạng thái hiệu lực."] if unknown else [])
            ),
        )
        turn_id = self._next_turn_id(session)
        tool_call = AgentToolCall(
            tool_call_id=self._next_tool_call_id(session),
            turn_id=turn_id,
            agent=AgentName.CITATION_VERIFIER_AGENT,
            tool_name="citation_status_check",
            input_summary=f"Verify status for {len(session.case.citations)} retrieved citations.",
            output_refs=dedupe(accepted + rejected + unknown),
            status=TurnStatus.NEEDS_REVIEW if rejected or unknown else TurnStatus.OK,
        )
        session.tool_calls.append(tool_call)
        self._append_turn(
            session,
            hearing_stage=HearingStage.CITATION_VERIFICATION,
            agent=AgentName.CITATION_VERIFIER_AGENT,
            message=(
                f"Citation Verifier giữ lại {len(accepted)} citation active "
                f"reject {len(rejected)} citation không phù hợp và flag {len(unknown)} citation unknown."
            ),
            citations_used=accepted,
            status=TurnStatus.NEEDS_REVIEW if rejected or unknown else TurnStatus.OK,
            tool_call_ids=[tool_call.tool_call_id],
        )
        self._append_audit(
            session,
            stage=AuditStage.VERIFICATION,
            severity=ClaimConfidence.MEDIUM if rejected or unknown else ClaimConfidence.LOW,
            message="Citation Verifier completed citation status checks.",
            related_citation_ids=dedupe(accepted + rejected + unknown),
        )

    def _advance_preliminary_assessment(self, session: HearingSession) -> None:
        if not session.fact_check:
            self._advance_fact_check(session)
        outcome = self._build_outcome_candidate(session)
        session.outcome_candidates = [outcome]
        turn_id = self._next_turn_id(session)
        tool_call = AgentToolCall(
            tool_call_id=self._next_tool_call_id(session),
            turn_id=turn_id,
            agent=AgentName.JUDGE_AGENT,
            tool_name="non_binding_outcome_guard",
            input_summary=(
                "Create and verify a non-binding proposed outcome candidate from grounded claims, "
                "evidence, citations, fact-check risk, and unresolved review items."
            ),
            output_refs=[outcome.outcome_id],
            status=TurnStatus.NEEDS_REVIEW,
        )
        session.tool_calls.append(tool_call)
        self._append_turn(
            session,
            hearing_stage=HearingStage.PRELIMINARY_ASSESSMENT,
            agent=AgentName.JUDGE_AGENT,
            message=(
                "Thẩm phán tạo một non-binding proposed outcome candidate để hỗ trợ human review; "
                "đây không phải phán quyết và không được xuất như quyết định của Tòa."
            ),
            claims=[claim.claim_id for claim in session.case.claims],
            evidence_used=outcome.evidence_ids,
            citations_used=outcome.citation_ids,
            status=TurnStatus.NEEDS_REVIEW,
            tool_call_ids=[tool_call.tool_call_id],
        )
        self._append_audit(
            session,
            stage=AuditStage.JUDICIAL_REVIEW,
            severity=outcome.risk_level,
            message=f"Generated non-binding proposed outcome candidate {outcome.outcome_id}.",
            related_claim_ids=outcome.supported_claim_ids,
            related_citation_ids=outcome.citation_ids,
            related_evidence_ids=outcome.evidence_ids,
        )

    def _advance_human_review(self, session: HearingSession) -> None:
        reasons = []
        if session.evidence_challenges:
            reasons.append("Evidence challenge remains unresolved.")
        unresolved_questions = [
            question for question in session.clarification_questions if question.status != TurnStatus.OK
        ]
        if unresolved_questions:
            reasons.append("Clarification questions remain unresolved.")
        if session.fact_check and session.fact_check.risk_level != ClaimConfidence.LOW:
            reasons.append("Fact-check risk requires reviewer approval.")
        if session.citation_verification and session.citation_verification.warnings:
            reasons.extend(session.citation_verification.warnings)
        if session.outcome_candidates:
            reasons.append("Non-binding proposed outcome requires human reviewer approval.")
        checklist = [
            "Đối chiếu nguyên văn hợp đồng và attachment.",
            "Kiểm tra điều kiện thanh toán còn lại.",
            "Xác minh citation từ nguồn văn bản chính thức.",
        ]
        checklist.extend(
            [
                f"Làm rõ {question.question_id}: {question.question}"
                for question in unresolved_questions
            ]
        )
        checklist.extend(
            [
                f"Review non-binding outcome {candidate.outcome_id}: {candidate.disposition.value}."
                for candidate in session.outcome_candidates
            ]
        )
        session.human_review = HumanReviewGate(
            required=True,
            blocked=True,
            reasons=dedupe(reasons),
            checklist=dedupe(checklist),
        )
        session.case.status = CaseStatus.REVIEW_REQUIRED
        session.status = CaseStatus.REVIEW_REQUIRED
        self._append_turn(
            session,
            hearing_stage=HearingStage.HUMAN_REVIEW,
            agent=AgentName.JUDGE_AGENT,
            message="Human review gate được kích hoạt trước khi xuất báo cáo V1.",
            status=TurnStatus.NEEDS_REVIEW,
        )
        self._append_audit(
            session,
            stage=AuditStage.HUMAN_REVIEW,
            severity=ClaimConfidence.MEDIUM,
            message="V1 hearing requires human review before final export.",
        )

    def _build_outcome_candidate(self, session: HearingSession) -> OutcomeCandidate:
        unresolved_questions = [
            question for question in session.clarification_questions if question.status != TurnStatus.OK
        ]
        accepted_citations = (
            session.citation_verification.accepted_citations
            if session.citation_verification
            else [citation.citation_id for citation in session.case.citations]
        )
        supported_claim_ids = [
            claim.claim_id
            for claim in session.case.claims
            if claim.evidence_ids and any(citation_id in accepted_citations for citation_id in claim.citation_ids)
        ]
        evidence_ids = dedupe(
            [
                evidence_id
                for claim in session.case.claims
                if claim.claim_id in supported_claim_ids
                for evidence_id in claim.evidence_ids
            ]
        )
        citation_ids = dedupe(
            [
                citation_id
                for claim in session.case.claims
                if claim.claim_id in supported_claim_ids
                for citation_id in claim.citation_ids
                if citation_id in accepted_citations
            ]
        )
        risk_level = session.fact_check.risk_level if session.fact_check else ClaimConfidence.MEDIUM
        if session.evidence_challenges or unresolved_questions or risk_level != ClaimConfidence.LOW:
            disposition = OutcomeDisposition.REQUIRES_MORE_EVIDENCE
            rationale = (
                "Non-binding proposed outcome: requires more evidence because the hearing still has "
                f"{len(session.evidence_challenges)} evidence challenge(s), "
                f"{len(unresolved_questions)} unresolved clarification question(s), "
                f"and fact-check risk `{risk_level.value}`. Human review must resolve these issues "
                "before this can be used as decision-support."
            )
        elif any(claim.speaker == AgentName.PLAINTIFF_AGENT for claim in session.case.claims):
            disposition = OutcomeDisposition.LIKELY_PLAINTIFF_FAVORED
            rationale = (
                "Non-binding proposed outcome: plaintiff-favored scenario is plausible only because "
                "the currently supported claims include evidence and accepted legal citations. "
                "Human review remains mandatory before export."
            )
        else:
            disposition = OutcomeDisposition.SPLIT_OR_UNCERTAIN
            rationale = (
                "Non-binding proposed outcome: split or uncertain because the current record does not "
                "support a single side strongly enough for decision-support."
            )

        candidate = OutcomeCandidate(
            outcome_id=f"OUTCOME_{len(session.outcome_candidates) + 1:03d}",
            disposition=disposition,
            rationale=rationale,
            supported_claim_ids=supported_claim_ids,
            evidence_ids=evidence_ids,
            citation_ids=citation_ids,
            risk_level=risk_level,
            requires_human_review=True,
            disclaimer=OUTCOME_DISCLAIMER,
        )
        guarded_text = f"{candidate.disposition.value} {candidate.rationale} {candidate.disclaimer}"
        if contains_official_judgment_language(guarded_text):
            violation = HarnessViolation(
                violation_id=self._next_violation_id(session),
                hearing_stage=HearingStage.PRELIMINARY_ASSESSMENT,
                agent=AgentName.JUDGE_AGENT,
                rule="no_official_judgment_language",
                message="Outcome candidate used official judgment language and was forced to human review.",
                severity=ClaimConfidence.HIGH,
                action=HarnessAction.HUMAN_REVIEW,
            )
            session.harness_violations.append(violation)
            candidate.disposition = OutcomeDisposition.REQUIRES_MORE_EVIDENCE
            candidate.rationale = (
                "Non-binding proposed outcome: requires more evidence and human review because the "
                "guard detected wording that could be confused with an official judgment."
            )
        return candidate

    def _advance_closing_record(self, session: HearingSession) -> None:
        session.case.agent_turns = []
        self._append_turn(
            session,
            hearing_stage=HearingStage.CLOSING_RECORD,
            agent=AgentName.CLERK_AGENT,
            message="Thư ký kết thúc phiên mô phỏng V1 và lưu transcript theo từng giai đoạn.",
            status=TurnStatus.OK,
        )


@lru_cache(maxsize=1)
def get_courtroom_v1_runtime_service() -> CourtroomV1RuntimeService:
    return CourtroomV1RuntimeService()
