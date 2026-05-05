export type CaseType = "civil_contract_dispute";
export type CaseStatus =
  | "draft"
  | "parsed"
  | "simulated"
  | "review_required"
  | "report_ready";

export type EvidenceType =
  | "contract"
  | "payment_receipt"
  | "message"
  | "statement"
  | "other";

export type EvidenceStatus = "uncontested" | "disputed" | "rejected";
export type ClaimConfidence = "low" | "medium" | "high";
export type EffectiveStatus = "active" | "expired" | "unknown";

export type AgentName =
  | "plaintiff_agent"
  | "prosecutor_agent"
  | "defense_agent"
  | "judge_agent"
  | "clerk_agent"
  | "legal_retrieval_agent"
  | "fact_check_agent"
  | "citation_verifier_agent";

export type TurnStatus =
  | "ok"
  | "needs_fact_check"
  | "needs_review"
  | "rejected";

export interface CaseAttachment {
  attachment_id: string;
  filename: string;
  media_type: string;
  note?: string | null;
}

export interface CaseFileInput {
  case_id: string;
  title: string;
  case_type: CaseType;
  language: string;
  narrative: string;
  attachments: CaseAttachment[];
}

export interface CaseCreateRequest {
  title: string;
  case_type: CaseType;
  language: string;
  narrative: string;
  attachments: CaseAttachment[];
}

export interface CaseRecord {
  case_id: string;
  title: string;
  case_type: CaseType;
  language: string;
  status: CaseStatus;
  attachment_count: number;
}

export interface CaseCreateResponse {
  case: CaseRecord;
}

export interface Fact {
  fact_id: string;
  content: string;
  source: string;
  confidence: ClaimConfidence;
}

export interface Evidence {
  evidence_id: string;
  type: EvidenceType;
  content: string;
  source: string;
  status: EvidenceStatus;
  used_by: string[];
  challenged_by: string[];
}

export interface LegalIssue {
  issue_id: string;
  title: string;
  description: string;
  tags: string[];
}

export interface Claim {
  claim_id: string;
  speaker: AgentName;
  content: string;
  evidence_ids: string[];
  citation_ids: string[];
  confidence: ClaimConfidence;
}

export interface Citation {
  citation_id: string;
  doc_id: string;
  title: string;
  article: string;
  clause?: string | null;
  content: string;
  retrieval_score: number;
  effective_status: EffectiveStatus;
  source: string;
}

export interface AgentTurn {
  turn_id: string;
  agent: AgentName;
  message: string;
  claims: string[];
  evidence_used: string[];
  citations_used: string[];
  status: TurnStatus;
}

export interface FactCheckResult {
  unsupported_claims: string[];
  contradictions: string[];
  citation_mismatches: string[];
  risk_level: ClaimConfidence;
}

export interface CitationVerificationResult {
  accepted_citations: string[];
  rejected_citations: string[];
  warnings: string[];
}

export interface JudgeSummary {
  summary: string;
  main_disputed_points: string[];
  questions_to_clarify: string[];
  unsupported_claims: string[];
  recommended_human_review: boolean;
}

export interface TrialMinutes {
  case_id: string;
  turn_ids: string[];
  minutes_markdown: string;
}

export interface FinalReport {
  case_id: string;
  case_summary: string;
  disputed_points: string[];
  human_review_checklist: string[];
  disclaimer: string;
}

export interface CaseState {
  case_id: string;
  title: string;
  case_type: CaseType;
  facts: Fact[];
  evidence: Evidence[];
  legal_issues: LegalIssue[];
  claims: Claim[];
  citations: Citation[];
  agent_turns: AgentTurn[];
  status: CaseStatus;
}

export interface ParseCaseResponse {
  case: CaseState;
}

export interface SimulationResponse {
  case: CaseState;
  fact_check: FactCheckResult;
  citation_verification: CitationVerificationResult;
  judge_summary: JudgeSummary;
  trial_minutes: TrialMinutes;
  final_report: FinalReport;
}

export interface ReportResponse {
  case_id: string;
  report_status: CaseStatus;
  generated_from_turns: string[];
  report: FinalReport;
}
