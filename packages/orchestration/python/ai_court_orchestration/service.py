from __future__ import annotations

from functools import lru_cache
from typing import TypedDict
import json
import re
import warnings

import httpx
from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)
from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from .llm import get_courtroom_llm_service
from packages.retrieval.python.ai_court_retrieval.service import (
    get_local_legal_retrieval_service,
)
from packages.shared.python.ai_court_shared.schemas import (
    AgentName,
    AgentTurn,
    CaseState,
    CaseStatus,
    Citation,
    CitationVerificationResult,
    Claim,
    ClaimConfidence,
    FactCheckResult,
    FinalReport,
    HumanReviewGate,
    JudgeSummary,
    LegalIssue,
    LegalSearchFilter,
    LegalSearchRequest,
    SimulationResponse,
    TrialMinutes,
    TurnStatus,
)

DISCLAIMER = (
    "This system is for legal education, simulation, and research support only. "
    "It does not replace qualified legal professionals."
)
CLAIM_NORMALIZE_PATTERN = re.compile(r"\s+")
ROLE_DRIFT_SPACE_PATTERN = re.compile(r"\s+")


class SimulationGraphState(TypedDict):
    case: CaseState
    claims: list[Claim]
    turns: list[AgentTurn]
    citations: list[Citation]
    issue_citations: dict[str, list[str]]
    fact_check: FactCheckResult | None
    citation_verification: CitationVerificationResult | None
    judge_summary: JudgeSummary | None
    trial_minutes: TrialMinutes | None
    final_report: FinalReport | None


def dedupe_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def normalize_claim_text(text: str) -> str:
    return CLAIM_NORMALIZE_PATTERN.sub(" ", text).strip().lower()


def normalize_role_text(text: str) -> str:
    return ROLE_DRIFT_SPACE_PATTERN.sub(" ", text).strip().lower()


def clamp_words(text: str, max_words: int) -> str:
    words = text.strip().split()
    if len(words) <= max_words:
        return text.strip()
    trimmed = " ".join(words[:max_words]).rstrip(",;:-")
    if not trimmed.endswith("."):
        trimmed += "..."
    return trimmed


def confidence_rank(value: ClaimConfidence) -> int:
    order = {
        ClaimConfidence.LOW: 0,
        ClaimConfidence.MEDIUM: 1,
        ClaimConfidence.HIGH: 2,
    }
    return order[value]


def merge_claims_by_content(claims: list[Claim], start_index: int) -> list[Claim]:
    merged: list[Claim] = []
    claim_index_by_key: dict[tuple[str, str], int] = {}

    for claim in claims:
        key = (claim.speaker.value, normalize_claim_text(claim.content))
        existing_index = claim_index_by_key.get(key)
        if existing_index is None:
            merged.append(
                Claim(
                    claim_id="",
                    speaker=claim.speaker,
                    content=claim.content,
                    evidence_ids=list(claim.evidence_ids),
                    citation_ids=list(claim.citation_ids),
                    confidence=claim.confidence,
                )
            )
            claim_index_by_key[key] = len(merged) - 1
            continue

        current = merged[existing_index]
        current.evidence_ids = dedupe_preserve(current.evidence_ids + claim.evidence_ids)
        current.citation_ids = dedupe_preserve(current.citation_ids + claim.citation_ids)
        if confidence_rank(claim.confidence) > confidence_rank(current.confidence):
            current.confidence = claim.confidence

    for offset, claim in enumerate(merged, start=start_index):
        claim.claim_id = f"CLAIM_{offset:03d}"
    return merged


def title_has_any(issue: LegalIssue, keywords: list[str]) -> bool:
    haystack = f"{issue.title} {issue.description}".lower()
    return any(keyword in haystack for keyword in keywords)


def clone_case(case_state: CaseState) -> CaseState:
    return CaseState.model_validate(case_state.model_dump(mode="json"))


class CourtroomSimulationService:
    def __init__(self) -> None:
        self.retrieval_service = get_local_legal_retrieval_service()
        self.llm_service = get_courtroom_llm_service()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(SimulationGraphState)
        builder.add_node("legal_retrieval", self._legal_retrieval_node)
        builder.add_node("plaintiff", self._plaintiff_node)
        builder.add_node("defense", self._defense_node)
        builder.add_node("judge", self._judge_node)
        builder.add_node("clerk", self._clerk_node)
        builder.set_entry_point("legal_retrieval")
        builder.add_edge("legal_retrieval", "plaintiff")
        builder.add_edge("plaintiff", "defense")
        builder.add_edge("defense", "judge")
        builder.add_edge("judge", "clerk")
        builder.add_edge("clerk", END)
        return builder.compile()

    def simulate(self, case_state: CaseState) -> SimulationResponse:
        working_case = clone_case(case_state)
        result = self.graph.invoke(
            {
                "case": working_case,
                "claims": [],
                "turns": [],
                "citations": [],
                "issue_citations": {},
                "fact_check": None,
                "citation_verification": None,
                "judge_summary": None,
                "trial_minutes": None,
                "final_report": None,
            }
        )
        simulated_case = result["case"]
        simulated_case.status = CaseStatus.SIMULATED
        simulated_case.claims = result["claims"]
        simulated_case.agent_turns = result["turns"]
        simulated_case.citations = result["citations"]
        return SimulationResponse(
            case=simulated_case,
            fact_check=result["fact_check"],
            citation_verification=result["citation_verification"],
            audit_trail=[],
            human_review=HumanReviewGate(required=False, blocked=False),
            judge_summary=result["judge_summary"],
            trial_minutes=result["trial_minutes"],
            final_report=result["final_report"],
        )

    def _legal_retrieval_node(self, state: SimulationGraphState) -> SimulationGraphState:
        case = state["case"]
        retrieved_citations: list[Citation] = []
        issue_citations: dict[str, list[str]] = {}
        for issue in case.legal_issues:
            query = f"{issue.title}. {issue.description}"
            response = self.retrieval_service.search(
                LegalSearchRequest(
                    query=query,
                    top_k=2,
                    filters=LegalSearchFilter(),
                )
            )
            issue_citations[issue.issue_id] = []
            for citation in response.citations:
                if citation.citation_id not in {item.citation_id for item in retrieved_citations}:
                    retrieved_citations.append(citation)
                issue_citations[issue.issue_id].append(citation.citation_id)

        retrieval_turn = AgentTurn(
            turn_id="TURN_001",
            agent=AgentName.LEGAL_RETRIEVAL_AGENT,
            message=(
                f"Legal retrieval gathered {len(retrieved_citations)} candidate citations "
                f"for {len(case.legal_issues)} legal issues."
            ),
            claims=[],
            evidence_used=[],
            citations_used=[citation.citation_id for citation in retrieved_citations],
            status=TurnStatus.OK,
        )
        state["citations"] = retrieved_citations
        state["issue_citations"] = issue_citations
        state["turns"] = [retrieval_turn]
        return state

    def _mark_evidence_usage(
        self,
        case: CaseState,
        evidence_ids: list[str],
        used_by: AgentName | None = None,
        challenged_by: AgentName | None = None,
    ) -> None:
        for evidence in case.evidence:
            if evidence.evidence_id not in evidence_ids:
                continue
            if used_by is not None and used_by.value not in evidence.used_by:
                evidence.used_by.append(used_by.value)
            if challenged_by is not None and challenged_by.value not in evidence.challenged_by:
                evidence.challenged_by.append(challenged_by.value)

    def _case_context_payload(self, case: CaseState) -> dict:
        return {
            "case_id": case.case_id,
            "title": case.title,
            "case_type": case.case_type.value,
            "legal_issues": [
                {
                    "issue_id": issue.issue_id,
                    "title": issue.title,
                    "description": issue.description,
                }
                for issue in case.legal_issues
            ],
            "facts": [
                {
                    "fact_id": fact.fact_id,
                    "content": fact.content,
                    "source": fact.source,
                }
                for fact in case.facts
            ],
            "evidence": [
                {
                    "evidence_id": evidence.evidence_id,
                    "type": evidence.type.value,
                    "content": evidence.content,
                    "status": evidence.status.value,
                    "source": evidence.source,
                }
                for evidence in case.evidence
            ],
        }

    def _citation_context_payload(
        self,
        citations: list[Citation],
        citation_ids: list[str] | None = None,
    ) -> list[dict]:
        selected = citations
        if citation_ids is not None:
            citation_id_set = set(citation_ids)
            selected = [citation for citation in citations if citation.citation_id in citation_id_set]
        return [
            {
                "citation_id": citation.citation_id,
                "article": citation.article,
                "title": citation.title,
                "content": citation.content,
                "effective_status": citation.effective_status.value,
            }
            for citation in selected
        ]

    def _llm_role_message(
        self,
        role: str,
        fallback_message: str,
        case: CaseState,
        claims: list[Claim],
        citations: list[Citation],
    ) -> str:
        if not self.llm_service.is_enabled():
            return clamp_words(fallback_message, self._role_message_max_words(role))

        role_instruction = self._role_instruction(role)
        max_words = self._role_message_max_words(role)
        system_prompt = (
            "You are helping a Vietnamese legal courtroom simulation. "
            "Return strict JSON only with shape {\"message\": string}. "
            "Write concise Vietnamese. Do not invent evidence or citations. "
            f"{role_instruction}"
        )
        user_prompt = json.dumps(
            {
                "task": f"Write the {role} turn message for the courtroom simulation.",
                "provider": self.llm_service.provider_label(),
                "case": self._case_context_payload(case),
                "claims": [
                    {
                        "claim_id": claim.claim_id,
                        "content": claim.content,
                        "confidence": claim.confidence.value,
                        "evidence_ids": claim.evidence_ids,
                        "citation_ids": claim.citation_ids,
                    }
                    for claim in claims
                ],
                "citations": self._citation_context_payload(citations),
                "requirements": [
                    "Use only the supplied facts, evidence, and citations.",
                    f"Keep the message under {max_words} words.",
                    "Sound like a courtroom participant, not a chatbot.",
                    self._role_requirement(role),
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        try:
            payload = self.llm_service.generate_json(system_prompt, user_prompt, max_tokens=512)
            message = str(payload.get("message", "")).strip()
            if not message:
                return clamp_words(fallback_message, max_words)
            if not self._role_message_is_valid(role, message):
                return clamp_words(fallback_message, max_words)
            return clamp_words(message, max_words)
        except Exception:
            return clamp_words(fallback_message, max_words)

    def _role_instruction(self, role: str) -> str:
        if role == "plaintiff":
            return (
                "You are speaking for the plaintiff. Advocate for the plaintiff's requests, "
                "but stay grounded in the supplied evidence and citations."
            )
        if role == "defense":
            return (
                "You are speaking for the defense. Do not argue that the defendant has already violated "
                "the contract unless that is explicitly part of the defense claims. Emphasize uncertainty, "
                "burden of proof, contract interpretation, or reasons the court should not conclude liability yet."
            )
        return "Stay consistent with the assigned courtroom role."

    def _role_requirement(self, role: str) -> str:
        if role == "plaintiff":
            return "Plaintiff stance only: ask the court to protect the buyer/plaintiff's claim."
        if role == "defense":
            return (
                "Defense stance only: do not ask the court to order the defendant to perform, refund, "
                "or compensate; instead ask the court to clarify terms, limit liability, or reject premature conclusions."
            )
        return "Remain consistent with the assigned side."

    def _role_message_max_words(self, role: str) -> int:
        if role == "plaintiff":
            return 52
        if role == "defense":
            return 42
        return 60

    def _role_message_is_valid(self, role: str, message: str) -> bool:
        normalized = normalize_role_text(message)
        if role == "defense":
            invalid_markers = [
                "bi don da vi pham",
                "ben ban da vi pham",
                "ong a da vi pham",
                "xin toa buoc bi don",
                "buoc bi don giao xe",
                "buoc bi don hoan tra",
                "nguyen don co quyen yeu cau",
            ]
            valid_markers = [
                "bi don",
                "de nghi",
                "lam ro",
                "chua du can cu",
                "chua the ket luan",
                "dieu kien thanh toan",
                "gia tri chung minh",
                "khong dong y",
            ]
            if any(marker in normalized for marker in invalid_markers):
                return False
            if not any(marker in normalized for marker in valid_markers):
                return False
        if role == "plaintiff":
            invalid_markers = [
                "chua du can cu ket luan bi don vi pham",
                "de nghi bac yeu cau cua nguyen don",
                "bi don khong vi pham",
            ]
            if any(marker in normalized for marker in invalid_markers):
                return False
        return True

    def _llm_judge_summary(
        self,
        case: CaseState,
        claims: list[Claim],
        citations: list[Citation],
        fact_check: FactCheckResult,
        fallback_summary: JudgeSummary,
    ) -> JudgeSummary:
        if not self.llm_service.is_enabled():
            return fallback_summary

        system_prompt = (
            "You are helping a Vietnamese legal courtroom simulation. "
            "Return strict JSON only with shape "
            "{\"summary\": string, \"main_disputed_points\": [string], "
            "\"questions_to_clarify\": [string]}. "
            "Do not invent facts, evidence, or legal conclusions."
        )
        user_prompt = json.dumps(
            {
                "task": "Draft a judge summary for the current simulation state.",
                "case": self._case_context_payload(case),
                "claims": [
                    {
                        "claim_id": claim.claim_id,
                        "speaker": claim.speaker.value,
                        "content": claim.content,
                        "confidence": claim.confidence.value,
                    }
                    for claim in claims
                ],
                "citations": self._citation_context_payload(citations),
                "fact_check": {
                    "risk_level": fact_check.risk_level.value,
                    "unsupported_claims": fact_check.unsupported_claims,
                    "contradictions": fact_check.contradictions,
                    "citation_mismatches": fact_check.citation_mismatches,
                },
                "requirements": [
                    "Write concise Vietnamese.",
                    "Keep disputed points grounded in legal issues and claims.",
                    "Keep questions focused on unresolved evidence or contract interpretation.",
                    "Do not decide a winner.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        try:
            payload = self.llm_service.generate_json(system_prompt, user_prompt, max_tokens=1536)
            return JudgeSummary(
                summary=str(payload.get("summary", fallback_summary.summary)).strip() or fallback_summary.summary,
                main_disputed_points=[
                    str(item).strip()
                    for item in payload.get("main_disputed_points", fallback_summary.main_disputed_points)
                    if str(item).strip()
                ] or fallback_summary.main_disputed_points,
                questions_to_clarify=[
                    str(item).strip()
                    for item in payload.get("questions_to_clarify", fallback_summary.questions_to_clarify)
                    if str(item).strip()
                ] or fallback_summary.questions_to_clarify,
                unsupported_claims=fallback_summary.unsupported_claims,
                recommended_human_review=fallback_summary.recommended_human_review,
            )
        except Exception:
            return fallback_summary

    def _llm_report_summary(
        self,
        case: CaseState,
        judge_summary: JudgeSummary | None,
        fallback_summary: str,
    ) -> str:
        if not self.llm_service.is_enabled() or judge_summary is None:
            return fallback_summary

        system_prompt = (
            "You are helping a Vietnamese legal courtroom simulation. "
            "Return strict JSON only with shape {\"case_summary\": string}. "
            "The summary must be neutral and concise."
        )
        user_prompt = json.dumps(
            {
                "task": "Draft the case summary paragraph for the final report.",
                "case": self._case_context_payload(case),
                "judge_summary": {
                    "summary": judge_summary.summary,
                    "main_disputed_points": judge_summary.main_disputed_points,
                    "questions_to_clarify": judge_summary.questions_to_clarify,
                },
                "requirements": [
                    "Write Vietnamese.",
                    "Keep the summary under 100 words.",
                    "Stay neutral and evidence-aware.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        try:
            payload = self.llm_service.generate_json(system_prompt, user_prompt, max_tokens=512)
            summary = str(payload.get("case_summary", "")).strip()
            return summary or fallback_summary
        except Exception:
            return fallback_summary

    def _build_plaintiff_claims(self, case: CaseState, issue_citations: dict[str, list[str]]) -> list[Claim]:
        claims: list[Claim] = []
        contract_evidence = [item.evidence_id for item in case.evidence if item.type == "contract"]
        payment_evidence = [item.evidence_id for item in case.evidence if item.type == "payment_receipt"]
        delivery_evidence = [
            item.evidence_id
            for item in case.evidence
            if item.type in {"message", "statement"} or "giao" in item.content.lower()
        ]
        for issue in case.legal_issues:
            citation_ids = issue_citations.get(issue.issue_id, [])[:2]
            if title_has_any(issue, ["giao", "delivery"]):
                claims.append(
                    Claim(
                        claim_id=f"CLAIM_{len(claims) + 1:03d}",
                        speaker=AgentName.PLAINTIFF_AGENT,
                        content="Nguyên đơn cho rằng bên bán đã vi phạm nghĩa vụ giao tài sản đúng hạn theo hợp đồng.",
                        evidence_ids=dedupe_preserve(contract_evidence + delivery_evidence),
                        citation_ids=citation_ids,
                        confidence=ClaimConfidence.HIGH,
                    )
                )
            elif title_has_any(issue, ["thanh toán", "payment", "hoàn", "bồi thường", "refund", "damages"]):
                claims.append(
                    Claim(
                        claim_id=f"CLAIM_{len(claims) + 1:03d}",
                        speaker=AgentName.PLAINTIFF_AGENT,
                        content="Nguyên đơn yêu cầu hoàn trả khoản đã thanh toán và xem xét bồi thường do việc chậm thực hiện hợp đồng.",
                        evidence_ids=dedupe_preserve(contract_evidence + payment_evidence + delivery_evidence),
                        citation_ids=citation_ids,
                        confidence=ClaimConfidence.MEDIUM,
                    )
                )
        return merge_claims_by_content(claims, start_index=1)

    def _plaintiff_node(self, state: SimulationGraphState) -> SimulationGraphState:
        case = state["case"]
        claims = list(state["claims"])
        plaintiff_claims = self._build_plaintiff_claims(case, state["issue_citations"])
        claims.extend(plaintiff_claims)
        evidence_used = dedupe_preserve(
            [evidence_id for claim in plaintiff_claims for evidence_id in claim.evidence_ids]
        )
        citations_used = dedupe_preserve(
            [citation_id for claim in plaintiff_claims for citation_id in claim.citation_ids]
        )
        self._mark_evidence_usage(case, evidence_used, used_by=AgentName.PLAINTIFF_AGENT)
        fallback_message = (
            "Nguyên đơn cho rằng bị đơn chậm giao xe trái hợp đồng, đề nghị Tòa buộc giao xe hoặc hoàn trả 28.000.000 đồng và xem xét bồi thường."
        )
        message = self._llm_role_message(
            role="plaintiff",
            fallback_message=fallback_message,
            case=case,
            claims=plaintiff_claims,
            citations=state["citations"],
        )
        state["claims"] = claims
        state["turns"].append(
            AgentTurn(
                turn_id=f"TURN_{len(state['turns']) + 1:03d}",
                agent=AgentName.PLAINTIFF_AGENT,
                message=message,
                claims=[claim.claim_id for claim in plaintiff_claims],
                evidence_used=evidence_used,
                citations_used=citations_used,
                status=TurnStatus.OK,
            )
        )
        return state

    def _build_defense_claims(self, case: CaseState, issue_citations: dict[str, list[str]], existing_claims: list[Claim]) -> list[Claim]:
        claims: list[Claim] = []
        contract_evidence = [item.evidence_id for item in case.evidence if item.type == "contract"]
        disputed_evidence = [item.evidence_id for item in case.evidence if item.status != "uncontested"]
        for issue in case.legal_issues:
            citation_ids = issue_citations.get(issue.issue_id, [])[:2]
            if title_has_any(issue, ["thanh toán", "payment"]):
                claims.append(
                    Claim(
                        claim_id=f"CLAIM_{len(existing_claims) + len(claims) + 1:03d}",
                        speaker=AgentName.DEFENSE_AGENT,
                        content="Bị đơn yêu cầu làm rõ điều kiện thanh toán còn lại trước khi kết luận có vi phạm nghĩa vụ giao tài sản hay không.",
                        evidence_ids=dedupe_preserve(contract_evidence + disputed_evidence),
                        citation_ids=citation_ids,
                        confidence=ClaimConfidence.MEDIUM,
                    )
                )
        if not claims:
            first_issue = case.legal_issues[0] if case.legal_issues else None
            citation_ids = state_issue_citations_fallback(issue_citations, first_issue.issue_id if first_issue else None)
            claims.append(
                Claim(
                    claim_id=f"CLAIM_{len(existing_claims) + 1:03d}",
                    speaker=AgentName.DEFENSE_AGENT,
                    content="Bị đơn đề nghị kiểm tra lại điều khoản hợp đồng và giá trị chứng minh của các chứng cứ đang bị tranh luận.",
                    evidence_ids=dedupe_preserve(contract_evidence + disputed_evidence),
                    citation_ids=citation_ids,
                    confidence=ClaimConfidence.MEDIUM,
                )
            )
        return merge_claims_by_content(claims, start_index=len(existing_claims) + 1)

    def _defense_node(self, state: SimulationGraphState) -> SimulationGraphState:
        case = state["case"]
        claims = list(state["claims"])
        defense_claims = self._build_defense_claims(case, state["issue_citations"], claims)
        claims.extend(defense_claims)
        evidence_used = dedupe_preserve(
            [evidence_id for claim in defense_claims for evidence_id in claim.evidence_ids]
        )
        citations_used = dedupe_preserve(
            [citation_id for claim in defense_claims for citation_id in claim.citation_ids]
        )
        self._mark_evidence_usage(case, evidence_used, used_by=AgentName.DEFENSE_AGENT)
        self._mark_evidence_usage(case, evidence_used, challenged_by=AgentName.DEFENSE_AGENT)
        status = TurnStatus.NEEDS_FACT_CHECK if any(item.status != "uncontested" for item in case.evidence) else TurnStatus.OK
        fallback_message = (
            "Bị đơn đề nghị Tòa làm rõ điều khoản thanh toán 30% còn lại và giá trị chứng minh của các chứng cứ narrative; hiện chưa đủ căn cứ kết luận bị đơn vi phạm."
        )
        message = self._llm_role_message(
            role="defense",
            fallback_message=fallback_message,
            case=case,
            claims=defense_claims,
            citations=state["citations"],
        )
        state["claims"] = claims
        state["turns"].append(
            AgentTurn(
                turn_id=f"TURN_{len(state['turns']) + 1:03d}",
                agent=AgentName.DEFENSE_AGENT,
                message=message,
                claims=[claim.claim_id for claim in defense_claims],
                evidence_used=evidence_used,
                citations_used=citations_used,
                status=status,
            )
        )
        return state

    def _build_fact_check(self, case: CaseState, claims: list[Claim], citations: list[Citation]) -> FactCheckResult:
        citation_ids = {citation.citation_id for citation in citations}
        unsupported_claims = [
            claim.claim_id
            for claim in claims
            if not claim.evidence_ids and not claim.citation_ids
        ]
        citation_mismatches = [
            claim.claim_id
            for claim in claims
            if any(citation_id not in citation_ids for citation_id in claim.citation_ids)
        ]
        contradictions: list[str] = []
        if any(item.status != "uncontested" for item in case.evidence):
            contradictions.append(
                "Một số chứng cứ narrative/message đang ở trạng thái disputed và cần đối chiếu thêm."
            )
        if any(claim.speaker == AgentName.DEFENSE_AGENT for claim in claims):
            contradictions.append(
                "Bị đơn yêu cầu làm rõ mối quan hệ giữa điều khoản thanh toán còn lại và nghĩa vụ giao tài sản."
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

    def _build_citation_verification(self, citations: list[Citation]) -> CitationVerificationResult:
        accepted = [citation.citation_id for citation in citations if citation.effective_status.value == "active"]
        rejected = [citation.citation_id for citation in citations if citation.effective_status.value == "expired"]
        warnings = []
        if any(citation.effective_status.value == "unknown" for citation in citations):
            warnings.append("Một số citation chưa xác định rõ trạng thái hiệu lực.")
        if citations:
            warnings.append("Cần đối chiếu citation từ nguồn văn bản chính thức trước khi dùng cho human review.")
        return CitationVerificationResult(
            accepted_citations=accepted,
            rejected_citations=rejected,
            warnings=warnings,
        )

    def _judge_node(self, state: SimulationGraphState) -> SimulationGraphState:
        case = state["case"]
        claims = state["claims"]
        citations = state["citations"]
        fact_check = self._build_fact_check(case, claims, citations)
        citation_verification = self._build_citation_verification(citations)
        disputed_points = [issue.title for issue in case.legal_issues]
        questions_to_clarify = []
        if any(item.status != "uncontested" for item in case.evidence):
            questions_to_clarify.append("Cần xác minh thêm các chứng cứ đang bị disputed, đặc biệt là message/narrative evidence.")
        if any(title_has_any(issue, ["thanh toán", "payment"]) for issue in case.legal_issues):
            questions_to_clarify.append("Điều khoản thanh toán còn lại có phải là điều kiện tiên quyết để giao tài sản hay không.")
        if any(title_has_any(issue, ["bồi thường", "damages", "hoàn", "refund"]) for issue in case.legal_issues):
            questions_to_clarify.append("Thiệt hại thực tế và khoản tiền yêu cầu hoàn trả cần được chứng minh thêm bằng chứng cứ bổ sung.")
        fallback_judge_summary = JudgeSummary(
            summary=(
                f"Vụ việc xoay quanh {', '.join(disputed_points).lower() if disputed_points else 'các nghĩa vụ hợp đồng'} "
                "và cần đối chiếu thêm điều khoản gốc cùng chứng cứ thực tế."
            ),
            main_disputed_points=disputed_points,
            questions_to_clarify=questions_to_clarify,
            unsupported_claims=fact_check.unsupported_claims,
            recommended_human_review=fact_check.risk_level != ClaimConfidence.LOW,
        )
        judge_summary = self._llm_judge_summary(
            case=case,
            claims=claims,
            citations=citations,
            fact_check=fact_check,
            fallback_summary=fallback_judge_summary,
        )
        state["fact_check"] = fact_check
        state["citation_verification"] = citation_verification
        state["judge_summary"] = judge_summary
        state["turns"].append(
            AgentTurn(
                turn_id=f"TURN_{len(state['turns']) + 1:03d}",
                agent=AgentName.JUDGE_AGENT,
                message="Thẩm phán tóm tắt các điểm tranh chấp chính và xác định các câu hỏi cần làm rõ thêm trước human review.",
                claims=[],
                evidence_used=[],
                citations_used=[citation.citation_id for citation in citations[:2]],
                status=TurnStatus.NEEDS_REVIEW if judge_summary.recommended_human_review else TurnStatus.OK,
            )
        )
        return state

    def _clerk_node(self, state: SimulationGraphState) -> SimulationGraphState:
        case = state["case"]
        judge_summary = state["judge_summary"]
        fact_check = state["fact_check"]
        clerk_turn = AgentTurn(
            turn_id=f"TURN_{len(state['turns']) + 1:03d}",
            agent=AgentName.CLERK_AGENT,
            message="Thư ký lập trial minutes và final report từ các lượt phát biểu cùng kết quả kiểm tra.",
            claims=[],
            evidence_used=[],
            citations_used=[],
            status=TurnStatus.OK,
        )
        state["turns"].append(clerk_turn)
        minutes_lines = ["## Trial Minutes", ""]
        for turn in state["turns"]:
            minutes_lines.append(
                f"- {turn.turn_id}: {turn.agent.value} | status={turn.status.value} | {turn.message}"
            )
        trial_minutes = TrialMinutes(
            case_id=case.case_id,
            turn_ids=[turn.turn_id for turn in state["turns"]],
            minutes_markdown="\n".join(minutes_lines),
        )
        checklist = [
            "Đối chiếu điều khoản nguyên văn trong hợp đồng và nội dung attachment đã trích xuất.",
            "Kiểm tra lại citation từ nguồn văn bản chính thức trước khi kết luận.",
        ]
        if fact_check and fact_check.contradictions:
            checklist.append("Làm rõ các mâu thuẫn về điều kiện thanh toán và nghĩa vụ giao tài sản.")
        fallback_case_summary = judge_summary.summary if judge_summary else case.title
        final_report = FinalReport(
            case_id=case.case_id,
            case_summary=self._llm_report_summary(case, judge_summary, fallback_case_summary),
            disputed_points=judge_summary.main_disputed_points if judge_summary else [],
            human_review_checklist=checklist,
            disclaimer=DISCLAIMER,
        )
        state["trial_minutes"] = trial_minutes
        state["final_report"] = final_report
        return state


def state_issue_citations_fallback(issue_citations: dict[str, list[str]], issue_id: str | None) -> list[str]:
    if issue_id and issue_id in issue_citations:
        return issue_citations[issue_id][:2]
    for citation_ids in issue_citations.values():
        if citation_ids:
            return citation_ids[:2]
    return []


@lru_cache(maxsize=1)
def get_courtroom_simulation_service() -> CourtroomSimulationService:
    return CourtroomSimulationService()
