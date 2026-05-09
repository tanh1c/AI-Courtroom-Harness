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
export type EvidenceAdmissibility =
  | "admitted"
  | "disputed"
  | "rejected"
  | "needs_review";
export type ClaimConfidence = "low" | "medium" | "high";
export type EffectiveStatus = "active" | "expired" | "unknown";
export type RetrievalStrategy = "bm25_local" | "hybrid" | "vector_only";

export type AgentName =
  | "plaintiff_agent"
  | "prosecutor_agent"
  | "defense_agent"
  | "judge_agent"
  | "clerk_agent"
  | "evidence_agent"
  | "legal_retrieval_agent"
  | "fact_check_agent"
  | "citation_verifier_agent";

export type HearingStage =
  | "opening"
  | "evidence_presentation"
  | "legal_retrieval"
  | "plaintiff_argument"
  | "defense_argument"
  | "evidence_challenge"
  | "judge_questions"
  | "party_responses"
  | "fact_check"
  | "citation_verification"
  | "preliminary_assessment"
  | "human_review"
  | "closing_record";

export type TurnStatus =
  | "ok"
  | "needs_fact_check"
  | "needs_review"
  | "rejected";

export type AuditStage =
  | "retrieval"
  | "argument"
  | "verification"
  | "judicial_review"
  | "reporting"
  | "human_review";

export type HumanReviewDecision = "approve" | "reject";
export type OutcomeDisposition =
  | "likely_plaintiff_favored"
  | "likely_defense_favored"
  | "split_or_uncertain"
  | "requires_more_evidence";

export type HarnessAction = "allow" | "block" | "repair" | "human_review";

export type AttachmentParseStatus =
  | "metadata_only"
  | "text_extracted"
  | "missing_file"
  | "unreadable";

export interface CaseAttachment {
  attachment_id: string;
  filename: string;
  media_type: string;
  note?: string | null;
  local_path?: string | null;
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

export interface CaseListResponse {
  cases: CaseRecord[];
}

export interface AttachmentParseResult {
  attachment_id: string;
  filename: string;
  media_type: string;
  note?: string | null;
  local_path?: string | null;
  detected_evidence_type: EvidenceType;
  extraction_status: AttachmentParseStatus;
  extracted_text_excerpt?: string | null;
  extracted_char_count: number;
  source: string;
  warnings: string[];
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

export interface LegalSearchFilter {
  linh_vuc: string[];
  loai_van_ban: string[];
  co_quan_ban_hanh: string[];
  effective_status: EffectiveStatus[];
}

export interface LegalSearchRequest {
  query: string;
  top_k: number;
  filters: LegalSearchFilter;
}

export interface LegalSearchResponse {
  citations: Citation[];
  query_strategy: RetrievalStrategy;
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

export interface V1AgentTurn extends AgentTurn {
  hearing_stage: HearingStage;
  tool_call_ids: string[];
}

export interface RolePermission {
  permission_id: string;
  hearing_stage: HearingStage;
  agent: AgentName;
  allowed: boolean;
  allowed_evidence_ids: string[];
  allowed_citation_ids: string[];
  requires_evidence: boolean;
  requires_citation: boolean;
  action_on_violation: HarnessAction;
  notes?: string | null;
}

export interface EvidenceChallenge {
  challenge_id: string;
  evidence_id: string;
  raised_by: AgentName;
  reason: string;
  admissibility: EvidenceAdmissibility;
  affected_claim_ids: string[];
  resolved_by?: AgentName | null;
  resolution_notes?: string | null;
}

export interface ClarificationQuestion {
  question_id: string;
  asked_by: AgentName;
  question: string;
  target_agents: AgentName[];
  related_claim_ids: string[];
  related_evidence_ids: string[];
  related_citation_ids: string[];
  status: TurnStatus;
}

export interface PartyResponse {
  response_id: string;
  question_id: string;
  responder: AgentName;
  content: string;
  evidence_ids: string[];
  citation_ids: string[];
  status: TurnStatus;
}

export interface OutcomeCandidate {
  outcome_id: string;
  disposition: OutcomeDisposition;
  rationale: string;
  supported_claim_ids: string[];
  evidence_ids: string[];
  citation_ids: string[];
  risk_level: ClaimConfidence;
  requires_human_review: boolean;
  disclaimer: string;
}

export interface AgentToolCall {
  tool_call_id: string;
  turn_id: string;
  agent: AgentName;
  tool_name: string;
  input_summary: string;
  output_refs: string[];
  status: TurnStatus;
}

export interface HarnessViolation {
  violation_id: string;
  hearing_stage: HearingStage;
  agent: AgentName;
  rule: string;
  message: string;
  severity: ClaimConfidence;
  action: HarnessAction;
  related_turn_id?: string | null;
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

export interface AuditEvent {
  event_id: string;
  stage: AuditStage;
  severity: ClaimConfidence;
  message: string;
  related_claim_ids: string[];
  related_citation_ids: string[];
  related_evidence_ids: string[];
}

export interface HumanReviewGate {
  required: boolean;
  blocked: boolean;
  reasons: string[];
  checklist: string[];
}

export interface HumanReviewRecord {
  reviewer_name: string;
  decision: HumanReviewDecision;
  notes?: string | null;
  checklist_updates: string[];
  resolved_at: string;
  status_after: CaseStatus;
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
  attachment_parses: AttachmentParseResult[];
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

export interface CaseDetailResponse {
  record: CaseRecord;
  case_input: CaseFileInput;
  parsed_case?: CaseState | null;
}

export interface HumanReviewRequest {
  reviewer_name: string;
  decision: HumanReviewDecision;
  notes?: string | null;
  checklist_updates: string[];
}

export interface SimulationResponse {
  case: CaseState;
  fact_check: FactCheckResult;
  citation_verification: CitationVerificationResult;
  audit_trail: AuditEvent[];
  human_review: HumanReviewGate;
  judge_summary: JudgeSummary;
  trial_minutes: TrialMinutes;
  final_report: FinalReport;
}

export interface HearingSession {
  session_id: string;
  case: CaseState;
  current_stage: HearingStage;
  stage_order: HearingStage[];
  role_permissions: RolePermission[];
  turns: V1AgentTurn[];
  tool_calls: AgentToolCall[];
  evidence_challenges: EvidenceChallenge[];
  clarification_questions: ClarificationQuestion[];
  party_responses: PartyResponse[];
  fact_check?: FactCheckResult | null;
  citation_verification?: CitationVerificationResult | null;
  outcome_candidates: OutcomeCandidate[];
  harness_violations: HarnessViolation[];
  audit_trail: AuditEvent[];
  human_review: HumanReviewGate;
  status: CaseStatus;
}

export interface HearingAdvanceRequest {
  expected_stage?: HearingStage | null;
}

export interface HearingEvidenceChallengesResponse {
  case_id: string;
  challenges: EvidenceChallenge[];
  evidence_agent_turns: V1AgentTurn[];
}

export interface HearingVerificationResponse {
  case_id: string;
  fact_check?: FactCheckResult | null;
  citation_verification?: CitationVerificationResult | null;
  verification_turns: V1AgentTurn[];
  tool_calls: AgentToolCall[];
}

export interface HearingOutcomeResponse {
  case_id: string;
  outcome_candidates: OutcomeCandidate[];
  preliminary_assessment_turns: V1AgentTurn[];
  harness_violations: HarnessViolation[];
  human_review: HumanReviewGate;
}

export interface AuditTrailResponse {
  case_id: string;
  audit_trail: AuditEvent[];
  human_review: HumanReviewGate;
}

export interface HumanReviewResponse {
  case_id: string;
  report_status: CaseStatus;
  human_review: HumanReviewGate;
  review_record: HumanReviewRecord;
  report: FinalReport;
}

export interface ReportResponse {
  case_id: string;
  report_status: CaseStatus;
  generated_from_turns: string[];
  report: FinalReport;
}

export interface MarkdownReportResponse {
  case_id: string;
  report_status: CaseStatus;
  markdown_path: string;
  markdown: string;
}

export interface HtmlReportResponse {
  case_id: string;
  report_status: CaseStatus;
  html_path: string;
  html: string;
}
