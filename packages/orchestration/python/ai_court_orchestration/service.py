from __future__ import annotations

from functools import lru_cache
from typing import TypedDict
import warnings

from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)
from langgraph.graph import END, StateGraph

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


def title_has_any(issue: LegalIssue, keywords: list[str]) -> bool:
    haystack = f"{issue.title} {issue.description}".lower()
    return any(keyword in haystack for keyword in keywords)


def clone_case(case_state: CaseState) -> CaseState:
    return CaseState.model_validate(case_state.model_dump(mode="json"))


class CourtroomSimulationService:
    def __init__(self) -> None:
        self.retrieval_service = get_local_legal_retrieval_service()
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
        return claims

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
        state["claims"] = claims
        state["turns"].append(
            AgentTurn(
                turn_id=f"TURN_{len(state['turns']) + 1:03d}",
                agent=AgentName.PLAINTIFF_AGENT,
                message="Nguyên đơn trình bày các yêu cầu về giao tài sản, hoàn tiền, và bồi thường trên cơ sở hợp đồng và chứng cứ thanh toán.",
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
        return claims

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
        state["claims"] = claims
        state["turns"].append(
            AgentTurn(
                turn_id=f"TURN_{len(state['turns']) + 1:03d}",
                agent=AgentName.DEFENSE_AGENT,
                message="Bị đơn phản hồi rằng cần làm rõ điều khoản thanh toán và giá trị chứng minh của các chứng cứ đang bị tranh luận.",
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
        judge_summary = JudgeSummary(
            summary=(
                f"Vụ việc xoay quanh {', '.join(disputed_points).lower() if disputed_points else 'các nghĩa vụ hợp đồng'} "
                "và cần đối chiếu thêm điều khoản gốc cùng chứng cứ thực tế."
            ),
            main_disputed_points=disputed_points,
            questions_to_clarify=questions_to_clarify,
            unsupported_claims=fact_check.unsupported_claims,
            recommended_human_review=fact_check.risk_level != ClaimConfidence.LOW,
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
        final_report = FinalReport(
            case_id=case.case_id,
            case_summary=judge_summary.summary if judge_summary else case.title,
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
