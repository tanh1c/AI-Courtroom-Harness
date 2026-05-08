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
    LEGAL_RETRIEVAL_AGENT = "legal_retrieval_agent"
    FACT_CHECK_AGENT = "fact_check_agent"
    CITATION_VERIFIER_AGENT = "citation_verifier_agent"


class TurnStatus(str, Enum):
    OK = "ok"
    NEEDS_FACT_CHECK = "needs_fact_check"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class AttachmentParseStatus(str, Enum):
    METADATA_ONLY = "metadata_only"
    TEXT_EXTRACTED = "text_extracted"
    MISSING_FILE = "missing_file"
    UNREADABLE = "unreadable"


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


class FactCheckResult(BaseModel):
    unsupported_claims: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    citation_mismatches: list[str] = Field(default_factory=list)
    risk_level: ClaimConfidence


class CitationVerificationResult(BaseModel):
    accepted_citations: list[str] = Field(default_factory=list)
    rejected_citations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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


class SimulationResponse(BaseModel):
    case: CaseState
    fact_check: FactCheckResult
    citation_verification: CitationVerificationResult
    judge_summary: JudgeSummary
    trial_minutes: TrialMinutes
    final_report: FinalReport


class ReportResponse(BaseModel):
    case_id: str
    report_status: CaseStatus
    generated_from_turns: list[str] = Field(default_factory=list)
    report: FinalReport
