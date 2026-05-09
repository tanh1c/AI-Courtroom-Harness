from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CaseType(str, Enum):
    CIVIL_CONTRACT_DISPUTE = "civil_contract_dispute"


class CaseStatus(str, Enum):
    DRAFT = "draft"
    PARSED = "parsed"
    SIMULATED = "simulated"
    REVIEW_REQUIRED = "review_required"
    REPORT_READY = "report_ready"


class EvidenceType(str, Enum):
    CONTRACT = "contract"
    PAYMENT_RECEIPT = "payment_receipt"
    MESSAGE = "message"
    STATEMENT = "statement"
    OTHER = "other"


class EvidenceStatus(str, Enum):
    UNCONTESTED = "uncontested"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class EvidenceAdmissibility(str, Enum):
    ADMITTED = "admitted"
    DISPUTED = "disputed"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class ClaimConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EffectiveStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class RetrievalStrategy(str, Enum):
    BM25_LOCAL = "bm25_local"
    HYBRID = "hybrid"
    VECTOR_ONLY = "vector_only"


class AgentName(str, Enum):
    PLAINTIFF_AGENT = "plaintiff_agent"
    PROSECUTOR_AGENT = "prosecutor_agent"
    DEFENSE_AGENT = "defense_agent"
    JUDGE_AGENT = "judge_agent"
    CLERK_AGENT = "clerk_agent"
    EVIDENCE_AGENT = "evidence_agent"
    LEGAL_RETRIEVAL_AGENT = "legal_retrieval_agent"
    FACT_CHECK_AGENT = "fact_check_agent"
    CITATION_VERIFIER_AGENT = "citation_verifier_agent"


class HearingStage(str, Enum):
    OPENING = "opening"
    EVIDENCE_PRESENTATION = "evidence_presentation"
    LEGAL_RETRIEVAL = "legal_retrieval"
    PLAINTIFF_ARGUMENT = "plaintiff_argument"
    DEFENSE_ARGUMENT = "defense_argument"
    EVIDENCE_CHALLENGE = "evidence_challenge"
    JUDGE_QUESTIONS = "judge_questions"
    PARTY_RESPONSES = "party_responses"
    FACT_CHECK = "fact_check"
    CITATION_VERIFICATION = "citation_verification"
    PRELIMINARY_ASSESSMENT = "preliminary_assessment"
    HUMAN_REVIEW = "human_review"
    CLOSING_RECORD = "closing_record"


class TurnStatus(str, Enum):
    OK = "ok"
    NEEDS_FACT_CHECK = "needs_fact_check"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class AuditStage(str, Enum):
    RETRIEVAL = "retrieval"
    ARGUMENT = "argument"
    VERIFICATION = "verification"
    JUDICIAL_REVIEW = "judicial_review"
    REPORTING = "reporting"
    HUMAN_REVIEW = "human_review"


class HumanReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class OutcomeDisposition(str, Enum):
    LIKELY_PLAINTIFF_FAVORED = "likely_plaintiff_favored"
    LIKELY_DEFENSE_FAVORED = "likely_defense_favored"
    SPLIT_OR_UNCERTAIN = "split_or_uncertain"
    REQUIRES_MORE_EVIDENCE = "requires_more_evidence"


class SimulatedDecisionDisposition(str, Enum):
    SIMULATED_PLAINTIFF_FAVORED = "simulated_plaintiff_favored"
    SIMULATED_DEFENSE_FAVORED = "simulated_defense_favored"
    SIMULATED_PARTIAL_RELIEF = "simulated_partial_relief"
    SIMULATED_RISKY_REQUIRES_REVIEW = "simulated_risky_requires_review"
    ADJOURNED_FOR_REVIEW = "adjourned_for_review"
    REQUIRES_MORE_EVIDENCE = "requires_more_evidence"
    NO_SIMULATED_DECISION = "no_simulated_decision"


class HarnessAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REPAIR = "repair"
    HUMAN_REVIEW = "human_review"


class AttachmentParseStatus(str, Enum):
    METADATA_ONLY = "metadata_only"
    TEXT_EXTRACTED = "text_extracted"
    MISSING_FILE = "missing_file"
    UNREADABLE = "unreadable"


class TrialProcedureStage(str, Enum):
    CASE_PREPARATION = "case_preparation"
    OPENING_FORMALITIES = "opening_formalities"
    APPEARANCE_CHECK = "appearance_check"
    PROCEDURE_EXPLANATION = "procedure_explanation"
    PLAINTIFF_CLAIM_STATEMENT = "plaintiff_claim_statement"
    DEFENSE_RESPONSE_STATEMENT = "defense_response_statement"
    EVIDENCE_EXAMINATION = "evidence_examination"
    JUDGE_EXAMINATION = "judge_examination"
    PLAINTIFF_DEBATE = "plaintiff_debate"
    DEFENSE_REBUTTAL = "defense_rebuttal"
    FINAL_STATEMENTS = "final_statements"
    DELIBERATION = "deliberation"
    SIMULATED_DECISION = "simulated_decision"
    CLOSING_RECORD = "closing_record"


class AppearanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    REPRESENTED = "represented"
    UNKNOWN = "unknown"


class HumanReviewMode(str, Enum):
    OPTIONAL = "optional"
    REQUIRED = "required"
    OFF = "off"


class CaseAttachment(BaseModel):
    attachment_id: str
    filename: str
    media_type: str
    note: str | None = None
    local_path: str | None = None


class CaseFileInput(BaseModel):
    case_id: str
    title: str
    case_type: CaseType
    language: str = "vi"
    narrative: str
    attachments: list[CaseAttachment] = Field(default_factory=list)


class CaseCreateRequest(BaseModel):
    title: str
    case_type: CaseType
    language: str = "vi"
    narrative: str
    attachments: list[CaseAttachment] = Field(default_factory=list)


class CaseRecord(BaseModel):
    case_id: str
    title: str
    case_type: CaseType
    language: str = "vi"
    status: CaseStatus
    attachment_count: int = 0


class CaseCreateResponse(BaseModel):
    case: CaseRecord


class CaseListResponse(BaseModel):
    cases: list[CaseRecord] = Field(default_factory=list)


class AttachmentParseResult(BaseModel):
    attachment_id: str
    filename: str
    media_type: str
    note: str | None = None
    local_path: str | None = None
    detected_evidence_type: EvidenceType
    extraction_status: AttachmentParseStatus
    extracted_text_excerpt: str | None = None
    extracted_char_count: int = 0
    source: str
    warnings: list[str] = Field(default_factory=list)


class Fact(BaseModel):
    fact_id: str
    content: str
    source: str
    confidence: ClaimConfidence


class Evidence(BaseModel):
    evidence_id: str
    type: EvidenceType
    content: str
    source: str
    status: EvidenceStatus
    used_by: list[str] = Field(default_factory=list)
    challenged_by: list[str] = Field(default_factory=list)


class LegalIssue(BaseModel):
    issue_id: str
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    claim_id: str
    speaker: AgentName
    content: str
    evidence_ids: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    confidence: ClaimConfidence


class Citation(BaseModel):
    citation_id: str
    doc_id: str
    title: str
    article: str
    clause: str | None = None
    content: str
    retrieval_score: float
    effective_status: EffectiveStatus
    source: str


class LegalSearchFilter(BaseModel):
    linh_vuc: list[str] = Field(default_factory=list)
    loai_van_ban: list[str] = Field(default_factory=list)
    co_quan_ban_hanh: list[str] = Field(default_factory=list)
    effective_status: list[EffectiveStatus] = Field(default_factory=list)


class LegalSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    filters: LegalSearchFilter = Field(default_factory=LegalSearchFilter)


class LegalSearchResponse(BaseModel):
    citations: list[Citation] = Field(default_factory=list)
    query_strategy: RetrievalStrategy


class RemoteVectorSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=50, ge=1, le=100)
    filters: LegalSearchFilter = Field(default_factory=LegalSearchFilter)


class RemoteVectorSearchResult(BaseModel):
    chunk_id: str
    score: float


class RemoteVectorSearchResponse(BaseModel):
    results: list[RemoteVectorSearchResult] = Field(default_factory=list)
    model_name: str


class AgentTurn(BaseModel):
    turn_id: str
    agent: AgentName
    message: str
    claims: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)
    citations_used: list[str] = Field(default_factory=list)
    status: TurnStatus


class V1AgentTurn(AgentTurn):
    hearing_stage: HearingStage
    tool_call_ids: list[str] = Field(default_factory=list)


class RolePermission(BaseModel):
    permission_id: str
    hearing_stage: HearingStage
    agent: AgentName
    allowed: bool = True
    allowed_evidence_ids: list[str] = Field(default_factory=list)
    allowed_citation_ids: list[str] = Field(default_factory=list)
    requires_evidence: bool = False
    requires_citation: bool = False
    action_on_violation: HarnessAction = HarnessAction.HUMAN_REVIEW
    notes: str | None = None


class EvidenceChallenge(BaseModel):
    challenge_id: str
    evidence_id: str
    raised_by: AgentName
    reason: str
    admissibility: EvidenceAdmissibility
    affected_claim_ids: list[str] = Field(default_factory=list)
    resolved_by: AgentName | None = None
    resolution_notes: str | None = None


class ClarificationQuestion(BaseModel):
    question_id: str
    asked_by: AgentName
    question: str
    target_agents: list[AgentName] = Field(default_factory=list)
    related_claim_ids: list[str] = Field(default_factory=list)
    related_evidence_ids: list[str] = Field(default_factory=list)
    related_citation_ids: list[str] = Field(default_factory=list)
    status: TurnStatus = TurnStatus.NEEDS_REVIEW


class PartyResponse(BaseModel):
    response_id: str
    question_id: str
    responder: AgentName
    content: str
    evidence_ids: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    status: TurnStatus = TurnStatus.OK


class OutcomeCandidate(BaseModel):
    outcome_id: str
    disposition: OutcomeDisposition
    rationale: str
    supported_claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    risk_level: ClaimConfidence
    requires_human_review: bool = True
    disclaimer: str


class AgentToolCall(BaseModel):
    tool_call_id: str
    turn_id: str
    agent: AgentName
    tool_name: str
    input_summary: str
    output_refs: list[str] = Field(default_factory=list)
    status: TurnStatus = TurnStatus.OK


class HarnessViolation(BaseModel):
    violation_id: str
    hearing_stage: HearingStage
    agent: AgentName
    rule: str
    message: str
    severity: ClaimConfidence
    action: HarnessAction
    related_turn_id: str | None = None


class FactCheckResult(BaseModel):
    unsupported_claims: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    citation_mismatches: list[str] = Field(default_factory=list)
    risk_level: ClaimConfidence


class CitationVerificationResult(BaseModel):
    accepted_citations: list[str] = Field(default_factory=list)
    rejected_citations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AuditEvent(BaseModel):
    event_id: str
    stage: AuditStage
    severity: ClaimConfidence
    message: str
    related_claim_ids: list[str] = Field(default_factory=list)
    related_citation_ids: list[str] = Field(default_factory=list)
    related_evidence_ids: list[str] = Field(default_factory=list)


class HumanReviewGate(BaseModel):
    required: bool
    blocked: bool
    reasons: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)


class HumanReviewRecord(BaseModel):
    reviewer_name: str
    decision: HumanReviewDecision
    notes: str | None = None
    checklist_updates: list[str] = Field(default_factory=list)
    resolved_at: str
    status_after: CaseStatus


class JudgeSummary(BaseModel):
    summary: str
    main_disputed_points: list[str] = Field(default_factory=list)
    questions_to_clarify: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    recommended_human_review: bool


class TrialMinutes(BaseModel):
    case_id: str
    turn_ids: list[str] = Field(default_factory=list)
    minutes_markdown: str


class FinalReport(BaseModel):
    case_id: str
    case_summary: str
    disputed_points: list[str] = Field(default_factory=list)
    human_review_checklist: list[str] = Field(default_factory=list)
    disclaimer: str


class CaseState(BaseModel):
    case_id: str
    title: str
    case_type: CaseType
    attachment_parses: list[AttachmentParseResult] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    legal_issues: list[LegalIssue] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    agent_turns: list[AgentTurn] = Field(default_factory=list)
    status: CaseStatus


class ParseCaseResponse(BaseModel):
    case: CaseState


class CaseDetailResponse(BaseModel):
    record: CaseRecord
    case_input: CaseFileInput
    parsed_case: CaseState | None = None


class HumanReviewRequest(BaseModel):
    reviewer_name: str
    decision: HumanReviewDecision
    notes: str | None = None
    checklist_updates: list[str] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    case: CaseState
    fact_check: FactCheckResult
    citation_verification: CitationVerificationResult
    audit_trail: list[AuditEvent] = Field(default_factory=list)
    human_review: HumanReviewGate = Field(
        default_factory=lambda: HumanReviewGate(required=False, blocked=False)
    )
    judge_summary: JudgeSummary
    trial_minutes: TrialMinutes
    final_report: FinalReport


class HearingSession(BaseModel):
    session_id: str
    case: CaseState
    current_stage: HearingStage
    stage_order: list[HearingStage] = Field(default_factory=list)
    role_permissions: list[RolePermission] = Field(default_factory=list)
    turns: list[V1AgentTurn] = Field(default_factory=list)
    tool_calls: list[AgentToolCall] = Field(default_factory=list)
    evidence_challenges: list[EvidenceChallenge] = Field(default_factory=list)
    clarification_questions: list[ClarificationQuestion] = Field(default_factory=list)
    party_responses: list[PartyResponse] = Field(default_factory=list)
    fact_check: FactCheckResult | None = None
    citation_verification: CitationVerificationResult | None = None
    outcome_candidates: list[OutcomeCandidate] = Field(default_factory=list)
    harness_violations: list[HarnessViolation] = Field(default_factory=list)
    audit_trail: list[AuditEvent] = Field(default_factory=list)
    human_review: HumanReviewGate = Field(
        default_factory=lambda: HumanReviewGate(required=True, blocked=True)
    )
    status: CaseStatus


class AppearanceRecord(BaseModel):
    appearance_id: str
    participant_role: AgentName
    display_name: str
    status: AppearanceStatus
    representative: str | None = None
    notes: str | None = None


class ProceduralAct(BaseModel):
    act_id: str
    trial_stage: TrialProcedureStage
    actor: AgentName
    label: str
    content: str
    required: bool = True
    completed: bool = True
    related_turn_ids: list[str] = Field(default_factory=list)


class CourtroomDialogueTurn(BaseModel):
    turn_id: str
    trial_stage: TrialProcedureStage
    speaker: AgentName
    speaker_label: str
    utterance: str
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    status: TurnStatus = TurnStatus.OK
    risk_notes: list[str] = Field(default_factory=list)


class EvidenceExamination(BaseModel):
    examination_id: str
    evidence_id: str
    introduced_by: AgentName
    plaintiff_position: str
    defense_position: str
    admissibility: EvidenceAdmissibility
    related_claim_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class DebateRound(BaseModel):
    debate_id: str
    topic: str
    plaintiff_turn_ids: list[str] = Field(default_factory=list)
    defense_turn_ids: list[str] = Field(default_factory=list)
    judge_summary: str
    unresolved_points: list[str] = Field(default_factory=list)


class FinalStatement(BaseModel):
    statement_id: str
    speaker: AgentName
    content: str
    requested_outcome: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)


class DeliberationRecord(BaseModel):
    deliberation_id: str
    established_facts: list[str] = Field(default_factory=list)
    disputed_facts: list[str] = Field(default_factory=list)
    legal_reasoning: list[str] = Field(default_factory=list)
    risk_level: ClaimConfidence
    related_claim_ids: list[str] = Field(default_factory=list)
    related_evidence_ids: list[str] = Field(default_factory=list)
    related_citation_ids: list[str] = Field(default_factory=list)


class DecisionGuardResult(BaseModel):
    guard_id: str
    human_review_mode: HumanReviewMode = HumanReviewMode.OPTIONAL
    allowed_to_emit: bool
    risk_level: ClaimConfidence
    blocked_official_language: bool = True
    unresolved_items: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SimulatedDecision(BaseModel):
    decision_id: str
    disposition: SimulatedDecisionDisposition
    summary: str
    relief_or_next_step: str
    rationale: list[str] = Field(default_factory=list)
    risk_level: ClaimConfidence
    non_binding_disclaimer: str
    supported_claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    requires_human_review: bool = False


class DialogueQualityReport(BaseModel):
    max_utterance_chars: int
    overlong_turn_ids: list[str] = Field(default_factory=list)
    ungrounded_turn_ids: list[str] = Field(default_factory=list)
    role_drift_warnings: list[str] = Field(default_factory=list)


class V2TrialSession(BaseModel):
    session_id: str
    case: CaseState
    current_stage: TrialProcedureStage
    stage_order: list[TrialProcedureStage] = Field(default_factory=list)
    human_review_mode: HumanReviewMode = HumanReviewMode.OPTIONAL
    appearances: list[AppearanceRecord] = Field(default_factory=list)
    procedural_acts: list[ProceduralAct] = Field(default_factory=list)
    dialogue_turns: list[CourtroomDialogueTurn] = Field(default_factory=list)
    evidence_examinations: list[EvidenceExamination] = Field(default_factory=list)
    debate_rounds: list[DebateRound] = Field(default_factory=list)
    final_statements: list[FinalStatement] = Field(default_factory=list)
    deliberation: DeliberationRecord | None = None
    decision_guard: DecisionGuardResult | None = None
    simulated_decision: SimulatedDecision | None = None
    fact_check: FactCheckResult | None = None
    citation_verification: CitationVerificationResult | None = None
    dialogue_quality: DialogueQualityReport = Field(
        default_factory=lambda: DialogueQualityReport(max_utterance_chars=280)
    )
    human_review: HumanReviewGate = Field(
        default_factory=lambda: HumanReviewGate(required=False, blocked=False)
    )
    status: CaseStatus


class V2TrialAdvanceRequest(BaseModel):
    expected_stage: TrialProcedureStage | None = None


class HearingAdvanceRequest(BaseModel):
    expected_stage: HearingStage | None = None


class HearingEvidenceChallengesResponse(BaseModel):
    case_id: str
    challenges: list[EvidenceChallenge] = Field(default_factory=list)
    evidence_agent_turns: list[V1AgentTurn] = Field(default_factory=list)


class HearingVerificationResponse(BaseModel):
    case_id: str
    fact_check: FactCheckResult | None = None
    citation_verification: CitationVerificationResult | None = None
    verification_turns: list[V1AgentTurn] = Field(default_factory=list)
    tool_calls: list[AgentToolCall] = Field(default_factory=list)


class HearingOutcomeResponse(BaseModel):
    case_id: str
    outcome_candidates: list[OutcomeCandidate] = Field(default_factory=list)
    preliminary_assessment_turns: list[V1AgentTurn] = Field(default_factory=list)
    harness_violations: list[HarnessViolation] = Field(default_factory=list)
    human_review: HumanReviewGate


class AuditTrailResponse(BaseModel):
    case_id: str
    audit_trail: list[AuditEvent] = Field(default_factory=list)
    human_review: HumanReviewGate


class HumanReviewResponse(BaseModel):
    case_id: str
    report_status: CaseStatus
    human_review: HumanReviewGate
    review_record: HumanReviewRecord
    report: FinalReport


class ReportResponse(BaseModel):
    case_id: str
    report_status: CaseStatus
    generated_from_turns: list[str] = Field(default_factory=list)
    report: FinalReport


class MarkdownReportResponse(BaseModel):
    case_id: str
    report_status: CaseStatus
    markdown_path: str
    markdown: str


class HtmlReportResponse(BaseModel):
    case_id: str
    report_status: CaseStatus
    html_path: str
    html: str
