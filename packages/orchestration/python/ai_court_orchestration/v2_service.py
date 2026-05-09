from __future__ import annotations

from functools import lru_cache

from packages.retrieval.python.ai_court_retrieval.service import (
    get_local_legal_retrieval_service,
)
from packages.shared.python.ai_court_shared.schemas import (
    AgentName,
    AppearanceRecord,
    AppearanceStatus,
    CaseState,
    CaseStatus,
    Citation,
    CitationVerificationResult,
    Claim,
    ClaimConfidence,
    CourtroomDialogueTurn,
    DebateRound,
    DecisionGuardResult,
    DeliberationRecord,
    DialogueQualityReport,
    EvidenceAdmissibility,
    EvidenceExamination,
    FactCheckResult,
    FinalStatement,
    HumanReviewGate,
    HumanReviewMode,
    LegalSearchFilter,
    LegalSearchRequest,
    ProceduralAct,
    SimulatedDecision,
    SimulatedDecisionDisposition,
    TrialProcedureStage,
    TurnStatus,
    V2TrialSession,
)


V2_STAGE_ORDER = [
    TrialProcedureStage.CASE_PREPARATION,
    TrialProcedureStage.OPENING_FORMALITIES,
    TrialProcedureStage.APPEARANCE_CHECK,
    TrialProcedureStage.PROCEDURE_EXPLANATION,
    TrialProcedureStage.PLAINTIFF_CLAIM_STATEMENT,
    TrialProcedureStage.DEFENSE_RESPONSE_STATEMENT,
    TrialProcedureStage.EVIDENCE_EXAMINATION,
    TrialProcedureStage.JUDGE_EXAMINATION,
    TrialProcedureStage.PLAINTIFF_DEBATE,
    TrialProcedureStage.DEFENSE_REBUTTAL,
    TrialProcedureStage.FINAL_STATEMENTS,
    TrialProcedureStage.DELIBERATION,
    TrialProcedureStage.SIMULATED_DECISION,
    TrialProcedureStage.CLOSING_RECORD,
]

V2_ALLOWED_SPEAKERS: dict[TrialProcedureStage, set[AgentName]] = {
    TrialProcedureStage.CASE_PREPARATION: {AgentName.CLERK_AGENT, AgentName.EVIDENCE_AGENT},
    TrialProcedureStage.OPENING_FORMALITIES: {AgentName.CLERK_AGENT},
    TrialProcedureStage.APPEARANCE_CHECK: {AgentName.CLERK_AGENT},
    TrialProcedureStage.PROCEDURE_EXPLANATION: {AgentName.JUDGE_AGENT},
    TrialProcedureStage.PLAINTIFF_CLAIM_STATEMENT: {AgentName.PLAINTIFF_AGENT},
    TrialProcedureStage.DEFENSE_RESPONSE_STATEMENT: {AgentName.DEFENSE_AGENT},
    TrialProcedureStage.EVIDENCE_EXAMINATION: {
        AgentName.JUDGE_AGENT,
        AgentName.EVIDENCE_AGENT,
        AgentName.PLAINTIFF_AGENT,
        AgentName.DEFENSE_AGENT,
    },
    TrialProcedureStage.JUDGE_EXAMINATION: {
        AgentName.JUDGE_AGENT,
        AgentName.PLAINTIFF_AGENT,
        AgentName.DEFENSE_AGENT,
    },
    TrialProcedureStage.PLAINTIFF_DEBATE: {AgentName.PLAINTIFF_AGENT},
    TrialProcedureStage.DEFENSE_REBUTTAL: {AgentName.DEFENSE_AGENT},
    TrialProcedureStage.FINAL_STATEMENTS: {AgentName.PLAINTIFF_AGENT, AgentName.DEFENSE_AGENT},
    TrialProcedureStage.DELIBERATION: {AgentName.JUDGE_AGENT},
    TrialProcedureStage.SIMULATED_DECISION: {AgentName.JUDGE_AGENT},
    TrialProcedureStage.CLOSING_RECORD: {AgentName.CLERK_AGENT},
}

SIMULATED_DECISION_DISCLAIMER = (
    "Kết quả này chỉ là mô phỏng không ràng buộc, không phải bản án, quyết định "
    "của Tòa án hoặc tư vấn pháp lý."
)

OFFICIAL_JUDGMENT_MARKERS = [
    "tòa tuyên",
    "tòa án tuyên",
    "tòa quyết định",
    "buộc bị đơn",
    "buộc nguyên đơn",
    "court orders",
    "the court hereby decides",
]

MAX_UTTERANCE_CHARS = 280

PARTY_GROUNDED_STAGES = {
    TrialProcedureStage.PLAINTIFF_CLAIM_STATEMENT,
    TrialProcedureStage.DEFENSE_RESPONSE_STATEMENT,
    TrialProcedureStage.EVIDENCE_EXAMINATION,
    TrialProcedureStage.JUDGE_EXAMINATION,
    TrialProcedureStage.PLAINTIFF_DEBATE,
    TrialProcedureStage.DEFENSE_REBUTTAL,
    TrialProcedureStage.FINAL_STATEMENTS,
}

ROLE_DRIFT_MARKERS = {
    AgentName.PLAINTIFF_AGENT: ["bị đơn:", "thẩm phán:", "thư ký:"],
    AgentName.DEFENSE_AGENT: ["nguyên đơn:", "thẩm phán:", "thư ký:"],
    AgentName.JUDGE_AGENT: ["nguyên đơn:", "bị đơn:", "thư ký:"],
    AgentName.CLERK_AGENT: ["nguyên đơn:", "bị đơn:", "thẩm phán:"],
}


class TrialRuntimeError(ValueError):
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


def contains_official_judgment_language(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in OFFICIAL_JUDGMENT_MARKERS)


def official_judgment_language_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in OFFICIAL_JUDGMENT_MARKERS if marker in lowered]


def compact_utterance(text: str, limit: int = MAX_UTTERANCE_CHARS) -> tuple[str, bool]:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized, False
    return normalized[: limit - 1].rstrip() + "…", True


def has_role_drift(speaker: AgentName, utterance: str) -> bool:
    lowered = utterance.lower()
    return any(marker in lowered for marker in ROLE_DRIFT_MARKERS.get(speaker, []))


def is_party_grounded(turn: CourtroomDialogueTurn) -> bool:
    if turn.speaker not in {AgentName.PLAINTIFF_AGENT, AgentName.DEFENSE_AGENT}:
        return True
    if turn.trial_stage not in PARTY_GROUNDED_STAGES:
        return True
    lowered = turn.utterance.lower()
    explicitly_missing = "chưa có chứng cứ" in lowered or "cần đối chiếu" in lowered
    return bool(turn.evidence_ids or turn.citation_ids or explicitly_missing)


class CourtroomV2RuntimeService:
    def __init__(self) -> None:
        self.retrieval_service = get_local_legal_retrieval_service()

    def start(
        self,
        case_state: CaseState,
        *,
        human_review_mode: HumanReviewMode = HumanReviewMode.OPTIONAL,
    ) -> V2TrialSession:
        case = clone_case(case_state)
        self._ensure_trial_grounding(case)
        case.status = CaseStatus.SIMULATED
        session = V2TrialSession(
            session_id=f"TRIAL_{case.case_id}",
            case=case,
            current_stage=TrialProcedureStage.CASE_PREPARATION,
            stage_order=V2_STAGE_ORDER,
            human_review_mode=human_review_mode,
            status=CaseStatus.SIMULATED,
        )
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.CASE_PREPARATION,
            speaker=AgentName.CLERK_AGENT,
            speaker_label="Thư ký",
            utterance="Thư ký tiếp nhận hồ sơ đã parse và lập lịch trình phiên tòa mô phỏng V2.",
        )
        self._append_act(
            session,
            trial_stage=TrialProcedureStage.CASE_PREPARATION,
            actor=AgentName.CLERK_AGENT,
            label="Chuẩn bị hồ sơ",
            content="Hồ sơ được chuyển vào runtime phiên tòa mô phỏng V2.",
            related_turn_ids=["TURN_001"],
        )
        return session

    def _ensure_trial_grounding(self, case: CaseState) -> None:
        if not case.citations:
            case.citations = self._retrieve_trial_citations(case)
        if not case.claims:
            evidence_ids = [evidence.evidence_id for evidence in case.evidence]
            citation_ids = [citation.citation_id for citation in case.citations]
            plaintiff_citations = citation_ids[:2]
            defense_citations = citation_ids[-2:] if len(citation_ids) > 1 else citation_ids
            case.claims = [
                Claim(
                    claim_id="CLAIM_001",
                    speaker=AgentName.PLAINTIFF_AGENT,
                    content="Nguyên đơn cho rằng bị đơn vi phạm nghĩa vụ giao tài sản đúng thời hạn.",
                    evidence_ids=evidence_ids[:2],
                    citation_ids=plaintiff_citations,
                    confidence=ClaimConfidence.HIGH if evidence_ids and plaintiff_citations else ClaimConfidence.MEDIUM,
                ),
                Claim(
                    claim_id="CLAIM_002",
                    speaker=AgentName.DEFENSE_AGENT,
                    content="Bị đơn yêu cầu làm rõ điều kiện thanh toán còn lại trước khi kết luận vi phạm.",
                    evidence_ids=evidence_ids[:1],
                    citation_ids=defense_citations,
                    confidence=ClaimConfidence.MEDIUM,
                ),
            ]

    def _retrieve_trial_citations(self, case: CaseState) -> list[Citation]:
        retrieved: list[Citation] = []
        queries = [
            f"{issue.title}. {issue.description}"
            for issue in case.legal_issues
        ] or [
            "nghĩa vụ giao tài sản đúng thời hạn trong hợp đồng mua bán",
            "điều kiện thanh toán còn lại trong hợp đồng mua bán",
        ]
        for query in queries:
            response = self.retrieval_service.search(
                LegalSearchRequest(
                    query=query,
                    top_k=2,
                    filters=LegalSearchFilter(),
                )
            )
            for citation in response.citations:
                if citation.citation_id not in {item.citation_id for item in retrieved}:
                    retrieved.append(citation)
        return retrieved

    def advance(
        self,
        session: V2TrialSession,
        expected_stage: TrialProcedureStage | None = None,
    ) -> V2TrialSession:
        next_stage = self._next_stage(session)
        if expected_stage is not None and expected_stage != next_stage:
            raise TrialRuntimeError(
                f"Invalid stage transition: expected {expected_stage.value}, next is {next_stage.value}."
            )
        handlers = {
            TrialProcedureStage.OPENING_FORMALITIES: self._advance_opening_formalities,
            TrialProcedureStage.APPEARANCE_CHECK: self._advance_appearance_check,
            TrialProcedureStage.PROCEDURE_EXPLANATION: self._advance_procedure_explanation,
            TrialProcedureStage.PLAINTIFF_CLAIM_STATEMENT: self._advance_plaintiff_claim_statement,
            TrialProcedureStage.DEFENSE_RESPONSE_STATEMENT: self._advance_defense_response_statement,
            TrialProcedureStage.EVIDENCE_EXAMINATION: self._advance_evidence_examination,
            TrialProcedureStage.JUDGE_EXAMINATION: self._advance_judge_examination,
            TrialProcedureStage.PLAINTIFF_DEBATE: self._advance_plaintiff_debate,
            TrialProcedureStage.DEFENSE_REBUTTAL: self._advance_defense_rebuttal,
            TrialProcedureStage.FINAL_STATEMENTS: self._advance_final_statements,
            TrialProcedureStage.DELIBERATION: self._advance_deliberation,
            TrialProcedureStage.SIMULATED_DECISION: self._advance_simulated_decision,
            TrialProcedureStage.CLOSING_RECORD: self._advance_closing_record,
        }
        handlers[next_stage](session)
        session.current_stage = next_stage
        return session

    def run_all(
        self,
        case_state: CaseState,
        *,
        human_review_mode: HumanReviewMode = HumanReviewMode.OPTIONAL,
    ) -> V2TrialSession:
        session = self.start(case_state, human_review_mode=human_review_mode)
        while session.current_stage != TrialProcedureStage.CLOSING_RECORD:
            session = self.advance(session)
        return session

    def assert_speaker_allowed(self, trial_stage: TrialProcedureStage, speaker: AgentName) -> None:
        allowed = V2_ALLOWED_SPEAKERS.get(trial_stage, set())
        if speaker not in allowed:
            allowed_values = ", ".join(sorted(agent.value for agent in allowed)) or "none"
            raise TrialRuntimeError(
                f"Speaker {speaker.value} is not allowed in {trial_stage.value}; allowed: {allowed_values}."
            )

    def _next_stage(self, session: V2TrialSession) -> TrialProcedureStage:
        try:
            current_index = session.stage_order.index(session.current_stage)
        except ValueError as exc:
            raise TrialRuntimeError(f"Unknown current stage: {session.current_stage.value}") from exc
        next_index = current_index + 1
        if next_index >= len(session.stage_order):
            raise TrialRuntimeError("V2 trial session is already at the final stage.")
        return session.stage_order[next_index]

    def _next_turn_id(self, session: V2TrialSession) -> str:
        return f"TURN_{len(session.dialogue_turns) + 1:03d}"

    def _next_act_id(self, session: V2TrialSession) -> str:
        return f"PACT_{len(session.procedural_acts) + 1:03d}"

    def _append_turn(
        self,
        session: V2TrialSession,
        *,
        trial_stage: TrialProcedureStage,
        speaker: AgentName,
        speaker_label: str,
        utterance: str,
        claim_ids: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        citation_ids: list[str] | None = None,
        status: TurnStatus = TurnStatus.OK,
        risk_notes: list[str] | None = None,
    ) -> CourtroomDialogueTurn:
        self.assert_speaker_allowed(trial_stage, speaker)
        compacted_utterance, was_compacted = compact_utterance(utterance)
        notes = list(risk_notes or [])
        if was_compacted:
            notes.append(f"Utterance compacted to {MAX_UTTERANCE_CHARS} characters for demo readability.")
        if has_role_drift(speaker, compacted_utterance):
            notes.append("Possible role drift detected in dialogue wording.")
        turn = CourtroomDialogueTurn(
            turn_id=self._next_turn_id(session),
            trial_stage=trial_stage,
            speaker=speaker,
            speaker_label=speaker_label,
            utterance=compacted_utterance,
            claim_ids=claim_ids or [],
            evidence_ids=evidence_ids or [],
            citation_ids=citation_ids or [],
            status=status,
            risk_notes=dedupe(notes),
        )
        session.dialogue_turns.append(turn)
        self._refresh_dialogue_quality(session)
        return turn

    def _refresh_dialogue_quality(self, session: V2TrialSession) -> None:
        overlong = [
            turn.turn_id
            for turn in session.dialogue_turns
            if len(turn.utterance) > MAX_UTTERANCE_CHARS
        ]
        ungrounded = [
            turn.turn_id
            for turn in session.dialogue_turns
            if not is_party_grounded(turn)
        ]
        role_drift = [
            f"{turn.turn_id}: {turn.speaker.value} wording may drift from assigned role"
            for turn in session.dialogue_turns
            if has_role_drift(turn.speaker, turn.utterance)
        ]
        session.dialogue_quality = DialogueQualityReport(
            max_utterance_chars=MAX_UTTERANCE_CHARS,
            overlong_turn_ids=overlong,
            ungrounded_turn_ids=ungrounded,
            role_drift_warnings=role_drift,
        )

    def _append_act(
        self,
        session: V2TrialSession,
        *,
        trial_stage: TrialProcedureStage,
        actor: AgentName,
        label: str,
        content: str,
        related_turn_ids: list[str],
    ) -> None:
        session.procedural_acts.append(
            ProceduralAct(
                act_id=self._next_act_id(session),
                trial_stage=trial_stage,
                actor=actor,
                label=label,
                content=content,
                related_turn_ids=related_turn_ids,
            )
        )

    def _claim_ids_for(self, session: V2TrialSession, agent: AgentName) -> list[str]:
        return [claim.claim_id for claim in session.case.claims if claim.speaker == agent]

    def _evidence_ids(self, session: V2TrialSession) -> list[str]:
        return [evidence.evidence_id for evidence in session.case.evidence]

    def _citation_ids(self, session: V2TrialSession) -> list[str]:
        return [citation.citation_id for citation in session.case.citations]

    def _advance_opening_formalities(self, session: V2TrialSession) -> None:
        turn = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.OPENING_FORMALITIES,
            speaker=AgentName.CLERK_AGENT,
            speaker_label="Thư ký",
            utterance=(
                f"Thư ký công bố mở phiên mô phỏng vụ {session.case.title}; "
                "phiên này chỉ phục vụ mô phỏng và học tập."
            ),
        )
        self._append_act(
            session,
            trial_stage=TrialProcedureStage.OPENING_FORMALITIES,
            actor=AgentName.CLERK_AGENT,
            label="Mở phiên",
            content="Thư ký công bố mở phiên tòa mô phỏng.",
            related_turn_ids=[turn.turn_id],
        )

    def _advance_appearance_check(self, session: V2TrialSession) -> None:
        session.appearances = [
            AppearanceRecord(
                appearance_id="APP_001",
                participant_role=AgentName.JUDGE_AGENT,
                display_name="Thẩm phán chủ tọa",
                status=AppearanceStatus.PRESENT,
            ),
            AppearanceRecord(
                appearance_id="APP_002",
                participant_role=AgentName.CLERK_AGENT,
                display_name="Thư ký phiên tòa",
                status=AppearanceStatus.PRESENT,
            ),
            AppearanceRecord(
                appearance_id="APP_003",
                participant_role=AgentName.PLAINTIFF_AGENT,
                display_name="Nguyên đơn",
                status=AppearanceStatus.PRESENT,
            ),
            AppearanceRecord(
                appearance_id="APP_004",
                participant_role=AgentName.DEFENSE_AGENT,
                display_name="Bị đơn",
                status=AppearanceStatus.PRESENT,
            ),
        ]
        turn = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.APPEARANCE_CHECK,
            speaker=AgentName.CLERK_AGENT,
            speaker_label="Thư ký",
            utterance="Thư ký kiểm tra sự có mặt: thẩm phán, thư ký, nguyên đơn và bị đơn đều có mặt.",
        )
        self._append_act(
            session,
            trial_stage=TrialProcedureStage.APPEARANCE_CHECK,
            actor=AgentName.CLERK_AGENT,
            label="Kiểm tra sự có mặt",
            content="Các chủ thể cần thiết đều có mặt trong phiên mô phỏng.",
            related_turn_ids=[turn.turn_id],
        )

    def _advance_procedure_explanation(self, session: V2TrialSession) -> None:
        turn = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.PROCEDURE_EXPLANATION,
            speaker=AgentName.JUDGE_AGENT,
            speaker_label="Thẩm phán",
            utterance=(
                "Thẩm phán giải thích trình tự: nguyên đơn trình bày, bị đơn đối đáp, "
                "xem xét chứng cứ, xét hỏi, tranh luận, nói lời sau cùng, nghị án mô phỏng "
                "và công bố kết quả không ràng buộc."
            ),
        )
        self._append_act(
            session,
            trial_stage=TrialProcedureStage.PROCEDURE_EXPLANATION,
            actor=AgentName.JUDGE_AGENT,
            label="Giải thích thủ tục",
            content="Thẩm phán nêu trình tự và giới hạn không ràng buộc của phiên mô phỏng.",
            related_turn_ids=[turn.turn_id],
        )

    def _advance_plaintiff_claim_statement(self, session: V2TrialSession) -> None:
        plaintiff_claims = self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT)
        evidence_ids = self._evidence_ids(session)[:2]
        citation_ids = self._citation_ids(session)[:1]
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.PLAINTIFF_CLAIM_STATEMENT,
            speaker=AgentName.PLAINTIFF_AGENT,
            speaker_label="Nguyên đơn",
            utterance=(
                "Nguyên đơn trình bày đã thanh toán theo hợp đồng nhưng bị đơn không giao tài sản "
                "đúng thời hạn, nên yêu cầu giao tài sản hoặc hoàn trả tiền."
            ),
            claim_ids=plaintiff_claims,
            evidence_ids=evidence_ids,
            citation_ids=citation_ids,
        )

    def _advance_defense_response_statement(self, session: V2TrialSession) -> None:
        defense_claims = self._claim_ids_for(session, AgentName.DEFENSE_AGENT)
        evidence_ids = self._evidence_ids(session)[:1]
        citation_ids = self._citation_ids(session)[-1:]
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.DEFENSE_RESPONSE_STATEMENT,
            speaker=AgentName.DEFENSE_AGENT,
            speaker_label="Bị đơn",
            utterance=(
                "Bị đơn đối đáp rằng cần làm rõ điều kiện thanh toán phần còn lại trước khi "
                "kết luận bên bán vi phạm nghĩa vụ giao tài sản."
            ),
            claim_ids=defense_claims,
            evidence_ids=evidence_ids,
            citation_ids=citation_ids,
            status=TurnStatus.NEEDS_FACT_CHECK,
            risk_notes=["Điều kiện thanh toán còn lại cần được đối chiếu với hợp đồng."],
        )

    def _advance_evidence_examination(self, session: V2TrialSession) -> None:
        evidence_ids = self._evidence_ids(session)
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.EVIDENCE_EXAMINATION,
            speaker=AgentName.EVIDENCE_AGENT,
            speaker_label="Bộ phận chứng cứ",
            utterance=f"Bộ phận chứng cứ trình bày {len(evidence_ids)} chứng cứ chính trong hồ sơ.",
            evidence_ids=evidence_ids,
            status=TurnStatus.NEEDS_REVIEW if self._has_disputed_evidence(session) else TurnStatus.OK,
            risk_notes=(["Có chứng cứ đang bị tranh chấp."] if self._has_disputed_evidence(session) else []),
        )
        session.evidence_examinations = []
        for evidence in session.case.evidence:
            disputed = evidence.status.value != "uncontested" or bool(evidence.challenged_by)
            related_claim_ids = [
                claim.claim_id
                for claim in session.case.claims
                if evidence.evidence_id in claim.evidence_ids
            ]
            self._append_turn(
                session,
                trial_stage=TrialProcedureStage.EVIDENCE_EXAMINATION,
                speaker=AgentName.JUDGE_AGENT,
                speaker_label="Thẩm phán",
                utterance=f"Thẩm phán đưa ra xem xét chứng cứ {evidence.evidence_id} và yêu cầu các bên nêu ý kiến.",
                claim_ids=related_claim_ids,
                evidence_ids=[evidence.evidence_id],
            )
            self._append_turn(
                session,
                trial_stage=TrialProcedureStage.EVIDENCE_EXAMINATION,
                speaker=AgentName.PLAINTIFF_AGENT,
                speaker_label="Nguyên đơn",
                utterance=(
                    f"Nguyên đơn đề nghị chấp nhận {evidence.evidence_id} vì chứng cứ này hỗ trợ "
                    "yêu cầu trong hồ sơ."
                ),
                claim_ids=[claim_id for claim_id in related_claim_ids if claim_id in self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT)],
                evidence_ids=[evidence.evidence_id],
                status=TurnStatus.NEEDS_REVIEW if disputed else TurnStatus.OK,
                risk_notes=(["Lập luận dựa trên chứng cứ cần review."] if disputed else []),
            )
            self._append_turn(
                session,
                trial_stage=TrialProcedureStage.EVIDENCE_EXAMINATION,
                speaker=AgentName.DEFENSE_AGENT,
                speaker_label="Bị đơn",
                utterance=(
                    f"Bị đơn {'đề nghị kiểm tra thêm bối cảnh của' if disputed else 'không tranh chấp trực tiếp'} "
                    f"{evidence.evidence_id} trong phạm vi phiên mô phỏng."
                ),
                claim_ids=[claim_id for claim_id in related_claim_ids if claim_id in self._claim_ids_for(session, AgentName.DEFENSE_AGENT)],
                evidence_ids=[evidence.evidence_id],
                status=TurnStatus.NEEDS_REVIEW if disputed else TurnStatus.OK,
                risk_notes=(["Defense challenge keeps this evidence review-pending."] if disputed else []),
            )
            session.evidence_examinations.append(
                EvidenceExamination(
                    examination_id=f"EXAM_{len(session.evidence_examinations) + 1:03d}",
                    evidence_id=evidence.evidence_id,
                    introduced_by=AgentName.EVIDENCE_AGENT,
                    plaintiff_position="Nguyên đơn đề nghị xem xét chứng cứ này để hỗ trợ yêu cầu.",
                    defense_position=(
                        "Bị đơn yêu cầu kiểm tra thêm tính xác thực và bối cảnh."
                        if disputed
                        else "Bị đơn không tranh chấp trực tiếp chứng cứ này trong demo."
                    ),
                    admissibility=EvidenceAdmissibility.NEEDS_REVIEW if disputed else EvidenceAdmissibility.ADMITTED,
                    related_claim_ids=related_claim_ids,
                    notes="Không dùng chứng cứ tranh chấp làm căn cứ duy nhất cho kết quả mô phỏng."
                    if disputed
                    else "Chứng cứ có thể được dùng làm căn cứ nền trong demo.",
                )
            )

    def _advance_judge_examination(self, session: V2TrialSession) -> None:
        evidence_ids = self._evidence_ids(session)
        citation_ids = self._citation_ids(session)[:1]
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.JUDGE_EXAMINATION,
            speaker=AgentName.JUDGE_AGENT,
            speaker_label="Thẩm phán",
            utterance="Thẩm phán hỏi nguyên đơn căn cứ nào xác định thời hạn giao tài sản là nghĩa vụ độc lập.",
            claim_ids=self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT),
            evidence_ids=evidence_ids[:1],
        )
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.JUDGE_EXAMINATION,
            speaker=AgentName.PLAINTIFF_AGENT,
            speaker_label="Nguyên đơn",
            utterance="Nguyên đơn trả lời rằng hợp đồng ghi rõ thời hạn giao tài sản và khoản tiền đã thanh toán.",
            claim_ids=self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT),
            evidence_ids=evidence_ids[:2],
            citation_ids=citation_ids,
        )
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.JUDGE_EXAMINATION,
            speaker=AgentName.JUDGE_AGENT,
            speaker_label="Thẩm phán",
            utterance="Thẩm phán hỏi bị đơn có chứng cứ trực tiếp về điều kiện thanh toán đủ trước khi giao hay không.",
            claim_ids=self._claim_ids_for(session, AgentName.DEFENSE_AGENT),
            evidence_ids=evidence_ids[-1:],
        )
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.JUDGE_EXAMINATION,
            speaker=AgentName.DEFENSE_AGENT,
            speaker_label="Bị đơn",
            utterance="Bị đơn cho rằng cần đối chiếu thêm trao đổi giữa hai bên trước khi kết luận lỗi.",
            claim_ids=self._claim_ids_for(session, AgentName.DEFENSE_AGENT),
            evidence_ids=evidence_ids[-1:],
            status=TurnStatus.NEEDS_REVIEW if self._has_disputed_evidence(session) else TurnStatus.OK,
            risk_notes=(["Một phần trả lời dựa trên chứng cứ cần review."] if self._has_disputed_evidence(session) else []),
        )

    def _advance_plaintiff_debate(self, session: V2TrialSession) -> None:
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.PLAINTIFF_DEBATE,
            speaker=AgentName.PLAINTIFF_AGENT,
            speaker_label="Nguyên đơn tranh luận",
            utterance=(
                "Nguyên đơn tranh luận rằng hợp đồng, khoản thanh toán và thời hạn giao tài sản "
                "đủ để xác định nghĩa vụ giao tài sản đúng hạn."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT),
            evidence_ids=self._evidence_ids(session)[:2],
            citation_ids=self._citation_ids(session)[:1],
        )
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.PLAINTIFF_DEBATE,
            speaker=AgentName.PLAINTIFF_AGENT,
            speaker_label="Nguyên đơn bổ sung tranh luận",
            utterance=(
                "Nguyên đơn đề nghị chỉ xem điều kiện thanh toán còn lại là điểm cần giải thích, "
                "không phải lý do phủ nhận toàn bộ nghĩa vụ giao tài sản."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT),
            evidence_ids=self._evidence_ids(session)[:1],
            citation_ids=self._citation_ids(session)[:1],
        )

    def _advance_defense_rebuttal(self, session: V2TrialSession) -> None:
        plaintiff_turn_ids = [
            turn.turn_id
            for turn in session.dialogue_turns
            if turn.trial_stage == TrialProcedureStage.PLAINTIFF_DEBATE
        ]
        defense_turn = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.DEFENSE_REBUTTAL,
            speaker=AgentName.DEFENSE_AGENT,
            speaker_label="Bị đơn đối đáp",
            utterance=(
                "Bị đơn đối đáp rằng không nên kết luận vượt quá phạm vi chứng cứ đã xác thực, "
                "đặc biệt với điều kiện thanh toán còn lại."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.DEFENSE_AGENT),
            evidence_ids=self._evidence_ids(session)[:1],
            citation_ids=self._citation_ids(session)[-1:],
            status=TurnStatus.NEEDS_FACT_CHECK,
            risk_notes=["Lập luận phòng vệ vẫn cần fact-check theo chứng cứ hợp đồng."],
        )
        defense_follow_up = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.DEFENSE_REBUTTAL,
            speaker=AgentName.DEFENSE_AGENT,
            speaker_label="Bị đơn bổ sung đối đáp",
            utterance=(
                "Bị đơn giữ quan điểm rằng chứng cứ về điều kiện thanh toán cần được đánh giá "
                "trước khi mô phỏng trách nhiệm bồi thường."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.DEFENSE_AGENT),
            evidence_ids=self._evidence_ids(session)[:1],
            citation_ids=self._citation_ids(session)[-1:],
            status=TurnStatus.NEEDS_FACT_CHECK,
            risk_notes=["Bồi thường vẫn thiếu chứng cứ định lượng."],
        )
        session.debate_rounds = [
            DebateRound(
                debate_id="DEBATE_001",
                topic="Nghĩa vụ giao tài sản đúng hạn và điều kiện thanh toán còn lại",
                plaintiff_turn_ids=plaintiff_turn_ids,
                defense_turn_ids=[defense_turn.turn_id, defense_follow_up.turn_id],
                judge_summary=(
                    "Tranh luận cho thấy nghĩa vụ giao tài sản có căn cứ ban đầu, "
                    "nhưng điều kiện thanh toán còn lại vẫn là điểm cần giải thích."
                ),
                unresolved_points=self._unresolved_items(session),
            )
        ]

    def _advance_final_statements(self, session: V2TrialSession) -> None:
        plaintiff_turn = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.FINAL_STATEMENTS,
            speaker=AgentName.PLAINTIFF_AGENT,
            speaker_label="Nguyên đơn nói lời sau cùng",
            utterance="Nguyên đơn giữ yêu cầu giao tài sản hoặc hoàn trả khoản tiền đã thanh toán.",
            claim_ids=self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT),
            evidence_ids=self._evidence_ids(session)[:2],
            citation_ids=self._citation_ids(session)[:1],
        )
        defense_turn = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.FINAL_STATEMENTS,
            speaker=AgentName.DEFENSE_AGENT,
            speaker_label="Bị đơn nói lời sau cùng",
            utterance="Bị đơn đề nghị ghi nhận các điểm chưa rõ trước khi đưa ra kết quả mô phỏng.",
            claim_ids=self._claim_ids_for(session, AgentName.DEFENSE_AGENT),
            evidence_ids=self._evidence_ids(session)[:1],
            citation_ids=self._citation_ids(session)[-1:],
            status=TurnStatus.NEEDS_REVIEW,
        )
        session.final_statements = [
            FinalStatement(
                statement_id="FINAL_001",
                speaker=AgentName.PLAINTIFF_AGENT,
                content=plaintiff_turn.utterance,
                requested_outcome="Giao tài sản hoặc hoàn trả tiền đã nhận.",
                evidence_ids=plaintiff_turn.evidence_ids,
                citation_ids=plaintiff_turn.citation_ids,
            ),
            FinalStatement(
                statement_id="FINAL_002",
                speaker=AgentName.DEFENSE_AGENT,
                content=defense_turn.utterance,
                requested_outcome="Không kết luận vượt quá chứng cứ đã xác thực.",
                evidence_ids=defense_turn.evidence_ids,
                citation_ids=defense_turn.citation_ids,
            ),
        ]

    def _advance_deliberation(self, session: V2TrialSession) -> None:
        fact_check = self._build_fact_check(session)
        citation_verification = self._build_citation_verification(session)
        session.fact_check = fact_check
        session.citation_verification = citation_verification
        disputed = self._unresolved_items(session)
        session.deliberation = DeliberationRecord(
            deliberation_id="DELIB_001",
            established_facts=self._established_facts(session),
            disputed_facts=disputed,
            legal_reasoning=self._legal_reasoning(session, citation_verification.accepted_citations),
            risk_level=fact_check.risk_level,
            related_claim_ids=[claim.claim_id for claim in session.case.claims],
            related_evidence_ids=self._evidence_ids(session),
            related_citation_ids=citation_verification.accepted_citations,
        )
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.DELIBERATION,
            speaker=AgentName.JUDGE_AGENT,
            speaker_label="Thẩm phán nghị án mô phỏng",
            utterance=(
                "Thẩm phán tổng hợp sự kiện đã rõ, điểm còn tranh chấp và căn cứ pháp lý "
                "trước khi tạo kết quả mô phỏng không ràng buộc."
            ),
            claim_ids=session.deliberation.related_claim_ids,
            evidence_ids=session.deliberation.related_evidence_ids,
            citation_ids=session.deliberation.related_citation_ids,
            status=TurnStatus.NEEDS_REVIEW if fact_check.risk_level != ClaimConfidence.LOW else TurnStatus.OK,
            risk_notes=disputed,
        )

    def _advance_simulated_decision(self, session: V2TrialSession) -> None:
        if session.deliberation is None:
            raise TrialRuntimeError("Cannot emit simulated decision before deliberation.")
        unresolved = self._unresolved_items(session)
        risk = session.deliberation.risk_level
        accepted_citations = (
            session.citation_verification.accepted_citations
            if session.citation_verification is not None
            else self._citation_ids(session)
        )
        grounded_claim_ids = self._grounded_claim_ids(session, accepted_citations)
        disposition = self._recommend_disposition(
            session,
            risk=risk,
            unresolved=unresolved,
            grounded_claim_ids=grounded_claim_ids,
            accepted_citations=accepted_citations,
        )
        guard = DecisionGuardResult(
            guard_id="GUARD_001",
            human_review_mode=session.human_review_mode,
            allowed_to_emit=disposition != SimulatedDecisionDisposition.NO_SIMULATED_DECISION,
            risk_level=risk,
            blocked_official_language=True,
            recommended_disposition=disposition,
            grounded_claim_ids=grounded_claim_ids,
            unresolved_items=unresolved,
            warnings=[
                "Decision must remain simulated and non-binding.",
                "Do not use official judgment language.",
            ],
        )
        if disposition == SimulatedDecisionDisposition.ADJOURNED_FOR_REVIEW:
            summary = "Phiên mô phỏng dừng ở hướng hoãn để review vì human review đang ở chế độ bắt buộc."
            relief = "Chuyển hồ sơ sang review trước khi mô phỏng kết quả sâu hơn."
            status = TurnStatus.NEEDS_REVIEW
        elif disposition == SimulatedDecisionDisposition.SIMULATED_PLAINTIFF_FAVORED:
            summary = "Kết quả mô phỏng nghiêng về việc nguyên đơn có căn cứ yêu cầu giao tài sản hoặc hoàn trả tiền."
            relief = "Mô phỏng hướng xử lý: giao tài sản theo hợp đồng hoặc hoàn trả khoản tiền đã nhận."
            status = TurnStatus.OK
        elif disposition == SimulatedDecisionDisposition.SIMULATED_PARTIAL_RELIEF:
            summary = "Kết quả mô phỏng chỉ ghi nhận một phần yêu cầu có căn cứ, các phần còn lại cần bổ sung chứng cứ."
            relief = "Mô phỏng hướng xử lý: xem xét phần giao tài sản hoặc hoàn trả tiền, chưa mô phỏng phần bồi thường."
            status = TurnStatus.NEEDS_REVIEW
        elif disposition == SimulatedDecisionDisposition.SIMULATED_RISKY_REQUIRES_REVIEW:
            summary = "Kết quả mô phỏng nghiêng về yêu cầu chính của nguyên đơn nhưng còn rủi ro chứng cứ."
            relief = "Mô phỏng hướng xử lý: ưu tiên giao tài sản hoặc hoàn trả tiền; phần bồi thường cần chứng cứ bổ sung."
            status = TurnStatus.NEEDS_REVIEW
        elif disposition == SimulatedDecisionDisposition.REQUIRES_MORE_EVIDENCE:
            summary = "Chưa đủ căn cứ để mô phỏng kết quả theo hướng một bên thắng rõ ràng."
            relief = "Cần bổ sung chứng cứ hoặc citation trước khi dùng kết quả ngoài demo."
            status = TurnStatus.NEEDS_REVIEW
        else:
            summary = "Không tạo kết quả mô phỏng vì decision guard chưa cho phép emit."
            relief = "Cần bổ sung căn cứ hoặc reviewer trước khi export."
            status = TurnStatus.REJECTED
        decision = SimulatedDecision(
            decision_id="SDEC_001",
            disposition=disposition,
            summary=summary,
            relief_or_next_step=relief,
            rationale=[
                "Hợp đồng và khoản thanh toán là căn cứ nền của phiên mô phỏng.",
                "Thời hạn giao tài sản được xem xét từ chứng cứ hợp đồng.",
                "Các điểm còn rủi ro được giữ trong checklist review thay vì bị bỏ qua.",
            ],
            risk_level=risk,
            non_binding_disclaimer=SIMULATED_DECISION_DISCLAIMER,
            supported_claim_ids=grounded_claim_ids,
            evidence_ids=self._grounded_evidence_ids(session, grounded_claim_ids),
            citation_ids=accepted_citations,
            requires_human_review=session.human_review_mode == HumanReviewMode.REQUIRED,
        )
        decision_text = f"{decision.summary} {decision.relief_or_next_step} {' '.join(decision.rationale)}"
        official_hits = official_judgment_language_hits(decision_text)
        if official_hits:
            guard.allowed_to_emit = False
            guard.official_language_hits = official_hits
            guard.warnings.append("Official judgment language was detected and blocked.")
            decision.disposition = SimulatedDecisionDisposition.NO_SIMULATED_DECISION
            decision.summary = "Không tạo kết quả mô phỏng vì guard phát hiện ngôn ngữ dễ nhầm với phán quyết chính thức."
            decision.relief_or_next_step = "Cần chỉnh prompt hoặc reviewer trước khi export."
            status = TurnStatus.REJECTED
        session.decision_guard = guard
        session.simulated_decision = decision
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.SIMULATED_DECISION,
            speaker=AgentName.JUDGE_AGENT,
            speaker_label="Thẩm phán công bố kết quả mô phỏng",
            utterance=f"{decision.summary} {decision.relief_or_next_step}",
            claim_ids=decision.supported_claim_ids,
            evidence_ids=decision.evidence_ids,
            citation_ids=decision.citation_ids,
            status=status,
            risk_notes=guard.unresolved_items + guard.warnings,
        )

    def _established_facts(self, session: V2TrialSession) -> list[str]:
        established = [
            fact.content
            for fact in session.case.facts
            if fact.confidence == ClaimConfidence.HIGH
        ]
        if not established:
            established = [
                fact.content
                for fact in session.case.facts
                if fact.confidence == ClaimConfidence.MEDIUM
            ]
        return established[:5]

    def _legal_reasoning(self, session: V2TrialSession, accepted_citations: list[str]) -> list[str]:
        reasoning = [
            "Established facts are separated from disputed or review-pending facts before any simulated outcome.",
            "Only active or accepted citations are carried into the simulated decision guard.",
        ]
        if accepted_citations:
            reasoning.append("The main delivery-duty claim is mapped to accepted citations and contract/payment evidence.")
        else:
            reasoning.append("No accepted citation is available, so the decision path must require more evidence.")
        if self._has_disputed_evidence(session):
            reasoning.append("Disputed evidence may inform risk notes but cannot be the sole basis for a simulated result.")
        return reasoning

    def _grounded_claim_ids(self, session: V2TrialSession, accepted_citations: list[str]) -> list[str]:
        accepted = set(accepted_citations)
        return [
            claim.claim_id
            for claim in session.case.claims
            if claim.evidence_ids and any(citation_id in accepted for citation_id in claim.citation_ids)
        ]

    def _grounded_evidence_ids(self, session: V2TrialSession, grounded_claim_ids: list[str]) -> list[str]:
        return dedupe(
            [
                evidence_id
                for claim in session.case.claims
                if claim.claim_id in grounded_claim_ids
                for evidence_id in claim.evidence_ids
            ]
        )

    def _recommend_disposition(
        self,
        session: V2TrialSession,
        *,
        risk: ClaimConfidence,
        unresolved: list[str],
        grounded_claim_ids: list[str],
        accepted_citations: list[str],
    ) -> SimulatedDecisionDisposition:
        if session.human_review_mode == HumanReviewMode.REQUIRED and unresolved:
            return SimulatedDecisionDisposition.ADJOURNED_FOR_REVIEW
        if not session.deliberation or not session.deliberation.established_facts:
            return SimulatedDecisionDisposition.NO_SIMULATED_DECISION
        if not accepted_citations or not grounded_claim_ids:
            return SimulatedDecisionDisposition.REQUIRES_MORE_EVIDENCE
        plaintiff_grounded = any(
            claim.claim_id in grounded_claim_ids and claim.speaker == AgentName.PLAINTIFF_AGENT
            for claim in session.case.claims
        )
        defense_grounded = any(
            claim.claim_id in grounded_claim_ids and claim.speaker == AgentName.DEFENSE_AGENT
            for claim in session.case.claims
        )
        if risk != ClaimConfidence.LOW and plaintiff_grounded:
            return SimulatedDecisionDisposition.SIMULATED_RISKY_REQUIRES_REVIEW
        if risk == ClaimConfidence.LOW and plaintiff_grounded and not defense_grounded:
            return SimulatedDecisionDisposition.SIMULATED_PLAINTIFF_FAVORED
        if risk == ClaimConfidence.LOW and defense_grounded and not plaintiff_grounded:
            return SimulatedDecisionDisposition.SIMULATED_DEFENSE_FAVORED
        if plaintiff_grounded and defense_grounded:
            return SimulatedDecisionDisposition.SIMULATED_PARTIAL_RELIEF
        return SimulatedDecisionDisposition.SIMULATED_RISKY_REQUIRES_REVIEW

    def _advance_closing_record(self, session: V2TrialSession) -> None:
        if session.simulated_decision is None:
            raise TrialRuntimeError("Cannot close V2 trial before simulated decision or safe stop.")
        review_required = (
            session.human_review_mode == HumanReviewMode.REQUIRED
            or (session.simulated_decision.risk_level != ClaimConfidence.LOW and session.human_review_mode != HumanReviewMode.OFF)
        )
        blocked = session.human_review_mode == HumanReviewMode.REQUIRED and review_required
        session.human_review = HumanReviewGate(
            required=review_required,
            blocked=blocked,
            reasons=(
                ["Human review is required by V2 runtime config."]
                if blocked
                else ["Human review is optional for V2 demo mode."] if review_required else []
            ),
            checklist=[
                f"Review unresolved item: {item}"
                for item in (session.decision_guard.unresolved_items if session.decision_guard else [])
            ],
        )
        session.status = CaseStatus.REVIEW_REQUIRED if blocked else CaseStatus.REPORT_READY
        session.case.status = session.status
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.CLOSING_RECORD,
            speaker=AgentName.CLERK_AGENT,
            speaker_label="Thư ký",
            utterance="Thư ký ghi nhận phiên mô phỏng V2 đã kết thúc và lưu biên bản theo thủ tục.",
        )

    def _has_disputed_evidence(self, session: V2TrialSession) -> bool:
        return any(evidence.status.value != "uncontested" or evidence.challenged_by for evidence in session.case.evidence)

    def _unresolved_items(self, session: V2TrialSession) -> list[str]:
        items: list[str] = []
        disputed = [
            evidence.evidence_id
            for evidence in session.case.evidence
            if evidence.status.value != "uncontested" or evidence.challenged_by
        ]
        if disputed:
            items.append(f"Chứng cứ cần review: {', '.join(disputed)}.")
        if any("bồi thường" in claim.content.lower() for claim in session.case.claims):
            items.append("Yêu cầu bồi thường cần chứng cứ định lượng.")
        if any(turn.status != TurnStatus.OK for turn in session.dialogue_turns):
            items.append("Một số lượt trình bày còn cần fact-check hoặc review.")
        return dedupe(items)

    def _build_fact_check(self, session: V2TrialSession) -> FactCheckResult:
        unsupported = [
            claim.claim_id
            for claim in session.case.claims
            if not claim.evidence_ids and not claim.citation_ids
        ]
        contradictions = self._unresolved_items(session)
        risk = ClaimConfidence.HIGH if unsupported else ClaimConfidence.MEDIUM if contradictions else ClaimConfidence.LOW
        return FactCheckResult(
            unsupported_claims=unsupported,
            contradictions=contradictions,
            citation_mismatches=[],
            risk_level=risk,
        )

    def _build_citation_verification(self, session: V2TrialSession) -> CitationVerificationResult:
        accepted = [
            citation.citation_id
            for citation in session.case.citations
            if citation.effective_status.value == "active"
        ]
        rejected = [
            citation.citation_id
            for citation in session.case.citations
            if citation.effective_status.value == "expired"
        ]
        warnings = ["Citation cần được đối chiếu nguồn chính thức nếu dùng ngoài demo."]
        return CitationVerificationResult(
            accepted_citations=accepted,
            rejected_citations=rejected,
            warnings=warnings,
        )


@lru_cache(maxsize=1)
def get_courtroom_v2_runtime_service() -> CourtroomV2RuntimeService:
    return CourtroomV2RuntimeService()
