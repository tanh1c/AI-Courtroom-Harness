from __future__ import annotations

import json
import os
from functools import lru_cache

from packages.orchestration.python.ai_court_orchestration.llm import (
    CourtroomLlmService,
    get_courtroom_llm_service,
)
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
    Evidence,
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

MAX_UTTERANCE_CHARS = 520

PARTY_GROUNDED_STAGES = {
    TrialProcedureStage.PLAINTIFF_CLAIM_STATEMENT,
    TrialProcedureStage.DEFENSE_RESPONSE_STATEMENT,
    TrialProcedureStage.EVIDENCE_EXAMINATION,
    TrialProcedureStage.JUDGE_EXAMINATION,
    TrialProcedureStage.PLAINTIFF_DEBATE,
    TrialProcedureStage.DEFENSE_REBUTTAL,
    TrialProcedureStage.FINAL_STATEMENTS,
}

V2_LLM_POLISH_STAGES = {
    TrialProcedureStage.PLAINTIFF_CLAIM_STATEMENT,
    TrialProcedureStage.DEFENSE_RESPONSE_STATEMENT,
    TrialProcedureStage.JUDGE_EXAMINATION,
    TrialProcedureStage.PLAINTIFF_DEBATE,
    TrialProcedureStage.DEFENSE_REBUTTAL,
    TrialProcedureStage.FINAL_STATEMENTS,
    TrialProcedureStage.SIMULATED_DECISION,
}

V2_LLM_POLISH_SPEAKERS = {
    AgentName.PLAINTIFF_AGENT,
    AgentName.DEFENSE_AGENT,
    AgentName.JUDGE_AGENT,
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
        self.llm_service: CourtroomLlmService = get_courtroom_llm_service()
        self.llm_polish_enabled = os.getenv("AI_COURT_V2_LLM_ENABLED", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.llm_polish_max_turns = int(os.getenv("AI_COURT_V2_LLM_MAX_TURNS", "12"))
        self.last_llm_polish_call_count = 0
        self.last_llm_provider_label = "heuristic"
        self._llm_polish_used_by_session: dict[str, int] = {}

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
        self._llm_polish_used_by_session[session.session_id] = 0
        self.last_llm_polish_call_count = 0
        self.last_llm_provider_label = "heuristic"
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.CASE_PREPARATION,
            speaker=AgentName.CLERK_AGENT,
            speaker_label="Thư ký",
            utterance=(
                "Hồ sơ đã được tiếp nhận. Thư ký kiểm tra danh mục tài liệu, đánh số chứng cứ "
                "và chuẩn bị đưa vụ việc vào phần hỏi đáp mô phỏng trước hội đồng."
            ),
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
                    content=(
                        "Nguyên đơn xác định bị đơn đã nhận tiền nhưng không giao tài sản "
                        "đúng hạn theo hợp đồng."
                    ),
                    evidence_ids=evidence_ids[:4] or evidence_ids,
                    citation_ids=plaintiff_citations,
                    confidence=ClaimConfidence.HIGH if evidence_ids and plaintiff_citations else ClaimConfidence.MEDIUM,
                ),
            ]
            if not self._has_strong_delivery_breach_record(case):
                case.claims.append(
                    Claim(
                        claim_id="CLAIM_002",
                        speaker=AgentName.DEFENSE_AGENT,
                        content="Bị đơn yêu cầu làm rõ điều kiện thanh toán còn lại trước khi kết luận vi phạm.",
                        evidence_ids=evidence_ids[:1],
                        citation_ids=defense_citations,
                        confidence=ClaimConfidence.MEDIUM,
                    )
                )

    def _case_text(self, case: CaseState) -> str:
        return " ".join(
            [
                case.title,
                *[fact.content for fact in case.facts],
                *[evidence.content for evidence in case.evidence],
            ]
        ).lower()

    def _has_strong_delivery_breach_record(self, case: CaseState) -> bool:
        text = self._case_text(case)
        required_markers = [
            ("hợp đồng", "hop dong"),
            ("chuyển khoản", "chuyen khoan"),
            ("chưa giao", "chua giao", "không giao", "khong giao"),
            ("thông báo", "thong bao", "khắc phục", "khac phuc"),
        ]
        return all(any(marker in text for marker in group) for group in required_markers)

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
        utterance = self._maybe_llm_polish_utterance(
            session,
            trial_stage=trial_stage,
            speaker=speaker,
            speaker_label=speaker_label,
            fallback_utterance=utterance,
            claim_ids=claim_ids or [],
            evidence_ids=evidence_ids or [],
            citation_ids=citation_ids or [],
        )
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

    def _maybe_llm_polish_utterance(
        self,
        session: V2TrialSession,
        *,
        trial_stage: TrialProcedureStage,
        speaker: AgentName,
        speaker_label: str,
        fallback_utterance: str,
        claim_ids: list[str],
        evidence_ids: list[str],
        citation_ids: list[str],
    ) -> str:
        if not self.llm_polish_enabled or not self.llm_service.is_enabled():
            return fallback_utterance
        if trial_stage not in V2_LLM_POLISH_STAGES or speaker not in V2_LLM_POLISH_SPEAKERS:
            return fallback_utterance
        used = self._llm_polish_used_by_session.get(session.session_id, 0)
        if used >= self.llm_polish_max_turns:
            return fallback_utterance

        system_prompt = (
            "You rewrite one Vietnamese courtroom-simulation utterance. "
            "Return strict JSON only with shape {\"utterance\": string}. "
            "Keep the same legal meaning and same procedural role. "
            "Do not invent facts, evidence, citations, admissions, deadlines, or remedies. "
            "Do not write official judgment language such as 'tòa tuyên' or 'buộc bị đơn'. "
            "Do not include speaker labels or colon-prefixed dialogue. "
            "Make it sound natural, cinematic, and courtroom-like while remaining concise."
        )
        user_prompt = json.dumps(
            {
                "case": {
                    "case_id": session.case.case_id,
                    "title": session.case.title,
                    "status": session.case.status.value,
                },
                "stage": trial_stage.value,
                "speaker": speaker.value,
                "speaker_label": speaker_label,
                "fallback_utterance": fallback_utterance,
                "related_claims": [
                    {
                        "claim_id": claim.claim_id,
                        "speaker": claim.speaker.value,
                        "content": claim.content,
                        "evidence_ids": claim.evidence_ids,
                        "citation_ids": claim.citation_ids,
                    }
                    for claim in session.case.claims
                    if claim.claim_id in set(claim_ids)
                ],
                "related_evidence": [
                    {
                        "evidence_id": evidence.evidence_id,
                        "type": evidence.type.value,
                        "status": evidence.status.value,
                        "content": evidence.content[:700],
                    }
                    for evidence in session.case.evidence
                    if evidence.evidence_id in set(evidence_ids)
                ],
                "related_citations": [
                    {
                        "citation_id": citation.citation_id,
                        "article": citation.article,
                        "title": citation.title,
                        "content": citation.content[:500],
                    }
                    for citation in session.case.citations
                    if citation.citation_id in set(citation_ids)
                ],
                "requirements": [
                    "Vietnamese only.",
                    "Maximum 90 words.",
                    "Preserve every legal limitation from the fallback utterance.",
                    "Use first person when the speaker is plaintiff_agent or defense_agent.",
                    "The judge may ask questions or announce a simulated non-binding result, but must not sound like an official court judgment.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        try:
            payload = self.llm_service.generate_json(system_prompt, user_prompt, max_tokens=320)
            polished = str(payload.get("utterance", "")).strip()
            if not polished:
                return fallback_utterance
            if contains_official_judgment_language(polished) or has_role_drift(speaker, polished):
                return fallback_utterance
            polished, _ = compact_utterance(polished, MAX_UTTERANCE_CHARS)
            self._llm_polish_used_by_session[session.session_id] = used + 1
            self.last_llm_polish_call_count = used + 1
            self.last_llm_provider_label = self.llm_service.provider_label()
            return polished
        except Exception:
            return fallback_utterance

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

    def _evidence_brief(self, evidence: Evidence) -> str:
        text = evidence.content.lower()
        if "chi phí" in text or "chi_phi" in text:
            return "bảng kê chi phí phát sinh, dùng riêng cho phần thiệt hại có chứng từ"
        if "chưa giao" in text or "chua_giao" in text:
            return "biên bản xác nhận sau hạn giao, ghi nhận tài sản vẫn chưa được bàn giao"
        if "thông báo" in text or "khắc phục" in text or "thong_bao" in text:
            return "thông báo khắc phục, thể hiện bên mua đã cho bên bán cơ hội giao tài sản hoặc hoàn tiền"
        if "chuyển khoản" in text or "chuyen_khoan" in text:
            return "chứng từ chuyển khoản, thể hiện số tiền đã đi từ bên mua sang bên bán"
        if "hợp đồng" in text or "hop_dong" in text:
            return "tài liệu hợp đồng, trong đó có giá mua bán, khoản trả trước, hạn giao và cách thanh toán phần còn lại"
        return "tài liệu trong hồ sơ, cần được đọc theo đúng nội dung trích xuất"

    def _plaintiff_evidence_position(self, evidence: Evidence) -> str:
        brief = self._evidence_brief(evidence)
        if "hợp đồng" in brief:
            return (
                f"Tôi đề nghị ghi nhận {evidence.evidence_id} là {brief}. Chính điều khoản này cho thấy tôi đã thanh toán trước "
                "và phần còn lại gắn với việc nhận xe, không phải điều kiện để bên bán giữ xe."
            )
        if "chuyển khoản" in brief:
            return (
                f"Với {evidence.evidence_id}, tôi xác nhận đây là khoản 28.000.000 đồng đã chuyển. "
                "Điểm này chứng minh tôi đã thực hiện phần thanh toán ban đầu theo hợp đồng."
            )
        if "chưa được bàn giao" in brief:
            return (
                f"{evidence.evidence_id} là biên bản lập sau hạn giao. Tôi dựa vào tài liệu này để chứng minh đến ngày đối chiếu, "
                "xe vẫn chưa được giao và tiền cũng chưa được hoàn lại."
            )
        if "khắc phục" in brief:
            return (
                f"Tài liệu {evidence.evidence_id} cho thấy tôi đã gửi thông báo, không phải im lặng rồi kiện ngay. "
                "Tôi đã cho bên bán thời hạn xử lý trước khi yêu cầu hoàn tiền."
            )
        if "chi phí phát sinh" in brief:
            return (
                f"Với {evidence.evidence_id}, tôi chỉ đề nghị xem khoản chi phí trong phạm vi hóa đơn mô phỏng. "
                "Nếu cần tách riêng mức bồi thường, tôi vẫn giữ yêu cầu chính về giao xe hoặc hoàn tiền."
            )
        return f"Tôi xác nhận tài liệu {evidence.evidence_id} đúng với hồ sơ tôi nộp và đề nghị được xem xét."

    def _defense_evidence_position(self, evidence: Evidence, disputed: bool) -> str:
        brief = self._evidence_brief(evidence)
        if disputed:
            return f"Tôi đề nghị kiểm tra thêm bối cảnh của {evidence.evidence_id}; tài liệu này chưa nên là căn cứ duy nhất."
        if "hợp đồng" in brief:
            return (
                f"Tôi không phản đối {evidence.evidence_id}. Nếu hợp đồng thể hiện phần còn lại thanh toán sau khi giao, "
                "tôi ghi nhận điểm phòng vệ về thanh toán trước bị thu hẹp."
            )
        if "chuyển khoản" in brief:
            return f"Tôi không phủ nhận đã nhận khoản tiền trong {evidence.evidence_id}; vấn đề còn lại là hệ quả của việc chậm giao."
        if "chưa được bàn giao" in brief:
            return (
                f"Tôi không phản đối trực tiếp {evidence.evidence_id}. Nếu biên bản được xem là xác thực, "
                "nó bất lợi cho lập luận rằng bên bán đã hoàn thành nghĩa vụ giao."
            )
        if "khắc phục" in brief:
            return f"Tôi ghi nhận có thông báo tại {evidence.evidence_id}; tôi chỉ đề nghị xem đúng thời hạn và nội dung được ghi."
        if "chi phí phát sinh" in brief:
            return (
                f"Tôi đề nghị tách {evidence.evidence_id} khỏi nghĩa vụ giao xe. Khoản chi phí có thể xem xét, "
                "nhưng phải dựa trên chứng từ và mức liên quan trực tiếp."
            )
        return f"Tôi không phản đối trực tiếp tài liệu {evidence.evidence_id} trong phạm vi phiên mô phỏng."

    def _advance_opening_formalities(self, session: V2TrialSession) -> None:
        turn = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.OPENING_FORMALITIES,
            speaker=AgentName.CLERK_AGENT,
            speaker_label="Thư ký",
            utterance=(
                f"Mời mọi người ổn định. Phiên mô phỏng vụ {session.case.title} bắt đầu; "
                "toàn bộ nội dung được ghi nhận để học tập và không có hiệu lực như bản án."
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
            utterance=(
                "Thư ký báo cáo: thẩm phán chủ tọa có mặt, thư ký có mặt, nguyên đơn có mặt, "
                "bị đơn có mặt. Không có yêu cầu hoãn phiên trong hồ sơ mô phỏng."
            ),
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
                "Trước khi đi vào nội dung, tôi nhắc lại trình tự. Nguyên đơn trình bày yêu cầu, "
                "bị đơn trả lời, sau đó chúng ta xem từng tài liệu, hỏi lại những điểm còn vênh, "
                "nghe tranh luận và lời sau cùng. Phần cuối chỉ là kết quả mô phỏng không ràng buộc."
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
                "Tôi đã ký hợp đồng, chuyển trước số tiền theo thỏa thuận và chờ đến hạn nhận xe. "
                "Đến thời điểm phải giao, xe vẫn không được bàn giao. Vì vậy tôi đề nghị ghi nhận "
                "việc bên bán vi phạm nghĩa vụ giao tài sản, trước hết là giao xe hoặc hoàn lại khoản đã nhận."
            ),
            claim_ids=plaintiff_claims,
            evidence_ids=evidence_ids,
            citation_ids=citation_ids,
        )

    def _advance_defense_response_statement(self, session: V2TrialSession) -> None:
        defense_claims = self._claim_ids_for(session, AgentName.DEFENSE_AGENT)
        evidence_ids = self._evidence_ids(session)[:1]
        citation_ids = self._citation_ids(session)[-1:]
        has_dispute = self._has_disputed_evidence(session)
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.DEFENSE_RESPONSE_STATEMENT,
            speaker=AgentName.DEFENSE_AGENT,
            speaker_label="Bị đơn",
            utterance=(
                "Tôi không phủ nhận có hợp đồng và khoản tiền đã nhận. Điều tôi muốn làm rõ là phần tiền còn lại "
                "và cách hai bên hiểu thời điểm thanh toán. Nếu hồ sơ thể hiện phần còn lại chỉ thanh toán sau khi giao xe, "
                "tôi sẽ không dựa vào điểm đó để phủ nhận toàn bộ nghĩa vụ giao."
            ),
            claim_ids=defense_claims,
            evidence_ids=evidence_ids,
            citation_ids=citation_ids,
            status=TurnStatus.NEEDS_FACT_CHECK if has_dispute else TurnStatus.OK,
            risk_notes=(["Điều kiện thanh toán còn lại cần được đối chiếu với hợp đồng."] if has_dispute else []),
        )

    def _advance_evidence_examination(self, session: V2TrialSession) -> None:
        evidence_ids = self._evidence_ids(session)
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.EVIDENCE_EXAMINATION,
            speaker=AgentName.EVIDENCE_AGENT,
            speaker_label="Bộ phận chứng cứ",
            utterance=(
                f"Hồ sơ hiện có {len(evidence_ids)} tài liệu được đánh số. Tôi sẽ đọc ngắn gọn từng tài liệu "
                "để các bên xác nhận đúng nội dung trước khi thẩm phán xét hỏi."
            ),
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
                utterance=(
                    f"Tài liệu {evidence.evidence_id} được đưa ra xem xét. Đây là {self._evidence_brief(evidence)}. "
                    "Các bên cho biết có phản đối tính xác thực hoặc cách hiểu nội dung không."
                ),
                claim_ids=related_claim_ids,
                evidence_ids=[evidence.evidence_id],
            )
            self._append_turn(
                session,
                trial_stage=TrialProcedureStage.EVIDENCE_EXAMINATION,
                speaker=AgentName.PLAINTIFF_AGENT,
                speaker_label="Nguyên đơn",
                utterance=self._plaintiff_evidence_position(evidence),
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
                utterance=self._defense_evidence_position(evidence, disputed),
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
                    plaintiff_position=self._plaintiff_evidence_position(evidence),
                    defense_position=(
                        "Bị đơn yêu cầu kiểm tra thêm tính xác thực và bối cảnh."
                        if disputed
                        else self._defense_evidence_position(evidence, disputed)
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
            utterance=(
                "Tôi hỏi nguyên đơn về các tài liệu đã nộp. Căn cứ nào cho thấy ngày giao tài sản đã được xác định rõ, "
                "và phần tiền còn lại không phải điều kiện phải hoàn tất trước khi giao?"
            ),
            claim_ids=self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT),
            evidence_ids=evidence_ids[:1],
        )
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.JUDGE_EXAMINATION,
            speaker=AgentName.PLAINTIFF_AGENT,
            speaker_label="Nguyên đơn",
            utterance=(
                "Trong hợp đồng có ngày giao tài sản và điều khoản thanh toán. Tôi đã chuyển trước theo đúng tỷ lệ. "
                "Phần còn lại được hiểu là thanh toán khi nhận xe, nên tôi không có lý do gì phải trả nốt trước khi xe được bàn giao."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT),
            evidence_ids=evidence_ids[:2],
            citation_ids=citation_ids,
        )
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.JUDGE_EXAMINATION,
            speaker=AgentName.JUDGE_AGENT,
            speaker_label="Thẩm phán",
            utterance=(
                "Tôi hỏi bị đơn về căn cứ phòng vệ. Ngoài cách anh hiểu hợp đồng, anh có tài liệu nào nói rõ bên mua phải thanh toán đủ 100% "
                "trước khi bên bán giao tài sản không?"
            ),
            claim_ids=self._claim_ids_for(session, AgentName.DEFENSE_AGENT),
            evidence_ids=evidence_ids[-1:],
        )
        self._append_turn(
            session,
            trial_stage=TrialProcedureStage.JUDGE_EXAMINATION,
            speaker=AgentName.DEFENSE_AGENT,
            speaker_label="Bị đơn",
            utterance=(
                "Ở thời điểm này tôi chưa xuất trình được tài liệu riêng ngoài bộ hồ sơ đã nộp. Tôi chỉ đề nghị đối chiếu câu chữ hợp đồng, "
                "nếu câu chữ không đặt điều kiện thanh toán trước thì điểm phòng vệ của tôi bị thu hẹp."
            ),
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
                "Từ hợp đồng, chứng từ chuyển khoản và biên bản xác nhận chưa giao, chuỗi sự kiện khá thẳng: "
                "tôi đã trả tiền trước, ngày giao đã qua, tài sản vẫn chưa được bàn giao. Tôi đề nghị không biến phần tiền còn lại "
                "thành điều kiện mới nếu hợp đồng không ghi như vậy."
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
                "Về chi phí phát sinh, tôi chỉ đề nghị xem xét trong phạm vi có chứng từ. Nếu phần nào chưa đủ thì có thể tách ra, "
                "nhưng nghĩa vụ giao xe hoặc hoàn lại tiền đã nhận thì đã có căn cứ rõ hơn."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT),
            evidence_ids=self._evidence_ids(session)[:1],
            citation_ids=self._citation_ids(session)[:1],
        )

    def _advance_defense_rebuttal(self, session: V2TrialSession) -> None:
        has_dispute = self._has_disputed_evidence(session)
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
                "Tôi ghi nhận các tài liệu đã được đọc. Nếu biên bản xác nhận chưa giao là đúng và hợp đồng không buộc thanh toán đủ trước, "
                "tôi không còn nhiều căn cứ để nói mình không có nghĩa vụ. Tôi chỉ đề nghị phần chi phí phát sinh phải dựa trên chứng từ cụ thể."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.DEFENSE_AGENT),
            evidence_ids=self._evidence_ids(session)[:1],
            citation_ids=self._citation_ids(session)[-1:],
            status=TurnStatus.NEEDS_FACT_CHECK if has_dispute else TurnStatus.OK,
            risk_notes=(["Lập luận phòng vệ vẫn cần fact-check theo chứng cứ hợp đồng."] if has_dispute else []),
        )
        defense_follow_up = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.DEFENSE_REBUTTAL,
            speaker=AgentName.DEFENSE_AGENT,
            speaker_label="Bị đơn bổ sung đối đáp",
            utterance=(
                "Nói ngắn gọn, tôi không tranh luận để kéo dài vụ việc. Tôi chỉ muốn phần kết luận phân biệt rõ: nghĩa vụ giao hoặc hoàn tiền là một chuyện, "
                "còn khoản bồi thường thêm thì cần chứng từ và mức thiệt hại cụ thể."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.DEFENSE_AGENT),
            evidence_ids=self._evidence_ids(session)[:1],
            citation_ids=self._citation_ids(session)[-1:],
            status=TurnStatus.NEEDS_FACT_CHECK if has_dispute else TurnStatus.OK,
            risk_notes=(["Bồi thường vẫn thiếu chứng cứ định lượng."] if has_dispute else []),
        )
        session.debate_rounds = [
            DebateRound(
                debate_id="DEBATE_001",
                topic="Nghĩa vụ giao tài sản đúng hạn và điều kiện thanh toán còn lại",
                plaintiff_turn_ids=plaintiff_turn_ids,
                defense_turn_ids=[defense_turn.turn_id, defense_follow_up.turn_id],
                judge_summary=(
                    "Tranh luận tập trung vào ba điểm: ngày giao tài sản, điều kiện thanh toán phần còn lại, "
                    "và mức chi phí phát sinh có chứng từ."
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
            utterance=(
                "Tôi chỉ mong sự việc được nhìn đúng theo giấy tờ. Tôi đã trả tiền, đã chờ đến hạn, và không nhận được tài sản. "
                "Nếu không giao được xe thì tôi đề nghị hoàn lại khoản tiền đã nhận; phần thiệt hại xin xem theo chứng từ."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.PLAINTIFF_AGENT),
            evidence_ids=self._evidence_ids(session)[:2],
            citation_ids=self._citation_ids(session)[:1],
        )
        defense_turn = self._append_turn(
            session,
            trial_stage=TrialProcedureStage.FINAL_STATEMENTS,
            speaker=AgentName.DEFENSE_AGENT,
            speaker_label="Bị đơn nói lời sau cùng",
            utterance=(
                "Tôi đề nghị ghi nhận đúng những gì hồ sơ thể hiện. Nếu kết quả mô phỏng nghiêng về nghĩa vụ giao hoặc hoàn tiền, "
                "tôi đề nghị vẫn giữ phần chi phí phát sinh trong phạm vi chứng từ đã kiểm tra."
            ),
            claim_ids=self._claim_ids_for(session, AgentName.DEFENSE_AGENT),
            evidence_ids=self._evidence_ids(session)[:1],
            citation_ids=self._citation_ids(session)[-1:],
            status=TurnStatus.NEEDS_REVIEW if self._has_disputed_evidence(session) else TurnStatus.OK,
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
                "Hội đồng mô phỏng tạm dừng để tổng hợp. Điểm đã rõ là hợp đồng, khoản tiền đã chuyển và tình trạng giao tài sản. "
                "Điểm cần cân nhắc là hệ quả của việc không giao đúng hạn và phần chi phí phát sinh có đủ chứng từ hay chưa."
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
            summary = (
                "Sau khi đối chiếu hồ sơ, hướng mô phỏng nghiêng về phía nguyên đơn vì "
                "bị đơn đã nhận tiền, thời hạn giao đã được xác định, nhưng tài sản chưa được bàn giao."
            )
            relief = (
                "Hướng xử lý trong demo là ưu tiên giao tài sản theo hợp đồng; nếu không thực hiện được, "
                "xem xét hoàn lại khoản tiền đã nhận. Phần chi phí phát sinh chỉ ghi nhận trong phạm vi chứng từ."
            )
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
                "Hợp đồng, chứng từ chuyển khoản và tài liệu về tình trạng chưa giao tạo thành chuỗi căn cứ chính.",
                "Điều kiện thanh toán phần còn lại được đọc theo nội dung tài liệu, không tự suy diễn thành điều kiện mới.",
                "Khoản chi phí phát sinh cần chứng từ định lượng riêng, nên được đánh giá tách khỏi nghĩa vụ giao hoặc hoàn tiền.",
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
            utterance=(
                "Thư ký ghi nhận phiên mô phỏng đã kết thúc. Biên bản, danh mục chứng cứ, phần tranh luận "
                "và kết quả mô phỏng không ràng buộc được lưu vào hồ sơ."
            ),
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
