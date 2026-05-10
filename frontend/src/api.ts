const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export type CaseRecord = {
  case_id: string;
  title: string;
  case_type: string;
  language: string;
  status: string;
  attachment_count: number;
};

export type CourtroomTurn = {
  turn_id: string;
  trial_stage: string;
  speaker: string;
  speaker_label: string;
  utterance: string;
  claim_ids: string[];
  evidence_ids: string[];
  citation_ids: string[];
  status: string;
  risk_notes: string[];
};

export type TimelineItem = {
  trial_stage: string;
  label: string;
  status: string;
  turn_ids: string[];
};

export type V2UiState = {
  case_id: string;
  session_id: string;
  current_stage: string;
  status: string;
  timeline: TimelineItem[];
  transcript: CourtroomTurn[];
  evidence_examinations: Array<{
    examination_id: string;
    evidence_id: string;
    plaintiff_position: string;
    defense_position: string;
    admissibility: string;
    notes?: string | null;
  }>;
  debate_rounds?: Array<{
    debate_id: string;
    topic: string;
    plaintiff_turn_ids: string[];
    defense_turn_ids: string[];
    judge_summary: string;
    unresolved_points: string[];
  }>;
  final_statements?: Array<{
    statement_id: string;
    speaker: string;
    content: string;
    requested_outcome?: string | null;
    evidence_ids: string[];
    citation_ids: string[];
  }>;
  deliberation?: {
    established_facts: string[];
    disputed_facts: string[];
    legal_reasoning: string[];
    risk_level: string;
  } | null;
  simulated_decision?: {
    disposition: string;
    summary: string;
    relief_or_next_step: string;
    rationale: string[];
    risk_level: string;
    evidence_ids: string[];
    citation_ids: string[];
  } | null;
  decision_guard?: {
    allowed_to_emit: boolean;
    grounded_claim_ids: string[];
    unresolved_items: string[];
    official_language_hits: string[];
    warnings: string[];
  } | null;
  human_review: {
    required: boolean;
    blocked: boolean;
    reasons: string[];
    checklist: string[];
  };
  dialogue_quality: {
    overlong_turn_ids: string[];
    ungrounded_turn_ids: string[];
    role_drift_warnings: string[];
  };
};

export type CaseDetail = {
  record: CaseRecord;
  case_input: {
    case_id: string;
    title: string;
    narrative: string;
    attachments: Array<{attachment_id: string; filename: string; note?: string | null}>;
  };
  parsed_case?: {
    facts: Array<{fact_id: string; content: string; confidence: string; source: string}>;
    evidence: Array<{evidence_id: string; type: string; content: string; source?: string; status: string}>;
    legal_issues: Array<{issue_id: string; title: string; description: string}>;
    claims: Array<{
      claim_id: string;
      speaker: string;
      content: string;
      evidence_ids: string[];
      citation_ids: string[];
      confidence: string;
    }>;
    citations: Array<{
      citation_id: string;
      article: string;
      title: string;
      content?: string;
      retrieval_score: number;
      effective_status?: string;
      source?: string;
    }>;
  } | null;
};

export type PipelineResult = {
  caseId: string;
  uiState: V2UiState;
  html?: string;
  htmlPath?: string;
  markdownPath?: string;
};

export type HumanReviewGate = {
  required: boolean;
  blocked: boolean;
  reasons: string[];
  checklist: string[];
};

export type AuditTrailResponse = {
  case_id: string;
  audit_trail: Array<{
    event_id: string;
    stage: string;
    severity: string;
    message: string;
    related_claim_ids: string[];
    related_citation_ids: string[];
    related_evidence_ids: string[];
  }>;
  human_review: HumanReviewGate;
};

export type SimulationResponse = {
  case: NonNullable<CaseDetail['parsed_case']> & {case_id: string; title: string; status: string};
  fact_check: {
    unsupported_claims: string[];
    contradictions: string[];
    citation_mismatches: string[];
    risk_level: string;
  };
  citation_verification: {
    accepted_citations: string[];
    rejected_citations: string[];
    warnings: string[];
  };
  audit_trail: AuditTrailResponse['audit_trail'];
  human_review: HumanReviewGate;
  judge_summary: {
    summary: string;
    main_disputed_points: string[];
    questions_to_clarify: string[];
    unsupported_claims: string[];
    recommended_human_review: boolean;
  };
  trial_minutes: {
    case_id: string;
    turn_ids: string[];
    minutes_markdown: string;
  };
  final_report: {
    case_id: string;
    case_summary: string;
    disputed_points: string[];
    human_review_checklist: string[];
    disclaimer: string;
  };
};

export type ReviewResponse = {
  case_id: string;
  report_status: string;
  human_review: HumanReviewGate;
  review_record: {
    reviewer_name: string;
    decision: string;
    notes?: string | null;
    checklist_updates: string[];
    resolved_at: string;
    status_after: string;
  };
  report: SimulationResponse['final_report'];
};

export type ReportResponse = {
  case_id: string;
  report_status: string;
  generated_from_turns: string[];
  report: SimulationResponse['final_report'];
};

export type V1Turn = {
  turn_id: string;
  agent: string;
  message: string;
  claims: string[];
  evidence_used: string[];
  citations_used: string[];
  status: string;
  hearing_stage: string;
  tool_call_ids: string[];
};

export type V1HearingSession = {
  session_id: string;
  case: NonNullable<CaseDetail['parsed_case']> & {case_id: string; title: string; status: string};
  current_stage: string;
  stage_order: string[];
  turns: V1Turn[];
  evidence_challenges: Array<{
    challenge_id: string;
    evidence_id: string;
    raised_by: string;
    reason: string;
    admissibility: string;
    affected_claim_ids: string[];
    resolution_notes?: string | null;
  }>;
  clarification_questions: Array<{
    question_id: string;
    asked_by: string;
    question: string;
    target_agents: string[];
    related_claim_ids: string[];
    related_evidence_ids: string[];
    related_citation_ids: string[];
    status: string;
  }>;
  party_responses: Array<{
    response_id: string;
    question_id: string;
    responder: string;
    content: string;
    evidence_ids: string[];
    citation_ids: string[];
    status: string;
  }>;
  fact_check?: SimulationResponse['fact_check'] | null;
  citation_verification?: SimulationResponse['citation_verification'] | null;
  outcome_candidates: Array<{
    outcome_id: string;
    disposition: string;
    rationale: string;
    supported_claim_ids: string[];
    evidence_ids: string[];
    citation_ids: string[];
    risk_level: string;
    requires_human_review: boolean;
    disclaimer: string;
  }>;
  harness_violations: Array<{
    violation_id: string;
    hearing_stage: string;
    agent: string;
    rule: string;
    message: string;
    severity: string;
    action: string;
    related_turn_id?: string | null;
  }>;
  human_review: HumanReviewGate;
  status: string;
};

export type V1ChallengesResponse = {
  case_id: string;
  challenges: V1HearingSession['evidence_challenges'];
  evidence_agent_turns: V1Turn[];
};

export type V1VerificationResponse = {
  case_id: string;
  fact_check?: SimulationResponse['fact_check'] | null;
  citation_verification?: SimulationResponse['citation_verification'] | null;
  verification_turns: V1Turn[];
  tool_calls: Array<{
    tool_call_id: string;
    turn_id: string;
    agent: string;
    tool_name: string;
    input_summary: string;
    output_refs: string[];
    status: string;
  }>;
};

export type V1OutcomeResponse = {
  case_id: string;
  outcome_candidates: V1HearingSession['outcome_candidates'];
  preliminary_assessment_turns: V1Turn[];
  harness_violations: V1HearingSession['harness_violations'];
  human_review: HumanReviewGate;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : {'Content-Type': 'application/json'}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function listCases(): Promise<CaseRecord[]> {
  const payload = await requestJson<{cases: CaseRecord[]}>('/api/v1/cases');
  return payload.cases;
}

export async function getCase(caseId: string): Promise<CaseDetail> {
  return requestJson<CaseDetail>(`/api/v1/cases/${caseId}`);
}

export async function createCase(title: string, narrative: string): Promise<CaseRecord> {
  const payload = await requestJson<{case: CaseRecord}>('/api/v1/cases', {
    method: 'POST',
    body: JSON.stringify({
      title,
      case_type: 'civil_contract_dispute',
      language: 'vi',
      narrative,
      attachments: [],
    }),
  });
  return payload.case;
}

export async function uploadAttachment(caseId: string, file: File, note?: string): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('note', note || file.name);
  await requestJson(`/api/v1/cases/${caseId}/attachments`, {
    method: 'POST',
    body: formData,
  });
}

export async function parseCase(caseId: string): Promise<void> {
  await requestJson(`/api/v1/cases/${caseId}/parse`, {method: 'POST'});
}

export async function simulateCase(caseId: string): Promise<SimulationResponse> {
  return requestJson<SimulationResponse>(`/api/v1/cases/${caseId}/simulate`, {method: 'POST'});
}

export async function getAuditTrail(caseId: string): Promise<AuditTrailResponse> {
  return requestJson<AuditTrailResponse>(`/api/v1/cases/${caseId}/audit`);
}

export async function reviewCase(options: {
  caseId: string;
  decision: 'approve' | 'reject';
  reviewerName: string;
  notes?: string;
  checklistUpdates?: string[];
}): Promise<ReviewResponse> {
  return requestJson<ReviewResponse>(`/api/v1/cases/${options.caseId}/review`, {
    method: 'POST',
    body: JSON.stringify({
      reviewer_name: options.reviewerName,
      decision: options.decision,
      notes: options.notes || null,
      checklist_updates: options.checklistUpdates || [],
    }),
  });
}

export async function getReport(caseId: string): Promise<ReportResponse> {
  return requestJson<ReportResponse>(`/api/v1/reports/${caseId}`);
}

export async function exportMvpMarkdown(caseId: string): Promise<{markdownPath: string; markdown: string}> {
  const payload = await requestJson<{markdown_path: string; markdown: string}>(`/api/v1/reports/${caseId}/markdown`, {
    method: 'POST',
  });
  return {markdownPath: payload.markdown_path, markdown: payload.markdown};
}

export async function startV1(caseId: string): Promise<V1HearingSession> {
  return requestJson<V1HearingSession>(`/api/v1/cases/${caseId}/hearing/start`, {method: 'POST'});
}

export async function advanceV1(caseId: string): Promise<V1HearingSession> {
  return requestJson<V1HearingSession>(`/api/v1/cases/${caseId}/hearing/advance`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export async function getV1Hearing(caseId: string): Promise<V1HearingSession> {
  return requestJson<V1HearingSession>(`/api/v1/cases/${caseId}/hearing`);
}

export async function getV1Challenges(caseId: string): Promise<V1ChallengesResponse> {
  return requestJson<V1ChallengesResponse>(`/api/v1/cases/${caseId}/evidence/challenges`);
}

export async function getV1Verification(caseId: string): Promise<V1VerificationResponse> {
  return requestJson<V1VerificationResponse>(`/api/v1/cases/${caseId}/verification`);
}

export async function getV1Outcome(caseId: string): Promise<V1OutcomeResponse> {
  return requestJson<V1OutcomeResponse>(`/api/v1/cases/${caseId}/outcome`);
}

export async function exportV1Markdown(caseId: string): Promise<string> {
  const payload = await requestJson<{markdown_path: string}>(`/api/v1/cases/${caseId}/hearing/record/markdown`, {
    method: 'POST',
  });
  return payload.markdown_path;
}

export async function exportV1Html(caseId: string): Promise<{htmlPath: string; html: string}> {
  const payload = await requestJson<{html_path: string; html: string}>(`/api/v1/cases/${caseId}/hearing/record/html`, {
    method: 'POST',
  });
  return {htmlPath: payload.html_path, html: payload.html};
}

export async function startV2(caseId: string): Promise<void> {
  await requestJson(`/api/v1/cases/${caseId}/trial-v2/start?human_review_mode=optional`, {method: 'POST'});
}

export async function advanceV2(caseId: string): Promise<V2UiState> {
  await requestJson(`/api/v1/cases/${caseId}/trial-v2/advance`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
  return getV2UiState(caseId);
}

export async function getV2UiState(caseId: string): Promise<V2UiState> {
  return requestJson<V2UiState>(`/api/v1/cases/${caseId}/trial-v2/ui-state`);
}

export async function exportV2Markdown(caseId: string): Promise<string> {
  const payload = await requestJson<{markdown_path: string}>(`/api/v1/cases/${caseId}/trial-v2/record/markdown`, {
    method: 'POST',
  });
  return payload.markdown_path;
}

export async function exportV2Html(caseId: string): Promise<{htmlPath: string; html: string}> {
  const payload = await requestJson<{html_path: string; html: string}>(`/api/v1/cases/${caseId}/trial-v2/record/html`, {
    method: 'POST',
  });
  return {htmlPath: payload.html_path, html: payload.html};
}

export async function runExistingV2Pipeline(
  caseId: string,
  onStep?: (message: string) => void,
): Promise<PipelineResult> {
  onStep?.('Parsing evidence and facts');
  await parseCase(caseId);
  onStep?.('Starting V2 trial');
  await startV2(caseId);

  let uiState = await getV2UiState(caseId);
  for (let index = 0; index < 20 && uiState.current_stage !== 'closing_record'; index += 1) {
    onStep?.(`Advancing stage ${index + 1}`);
    uiState = await advanceV2(caseId);
  }

  onStep?.('Exporting record');
  const markdownPath = await exportV2Markdown(caseId);
  const {htmlPath, html} = await exportV2Html(caseId);
  uiState = await getV2UiState(caseId);
  return {caseId, uiState, markdownPath, htmlPath, html};
}

export async function runV2Pipeline(options: {
  title: string;
  narrative: string;
  files: File[];
  onStep?: (message: string) => void;
}): Promise<PipelineResult> {
  options.onStep?.('Creating case');
  const record = await createCase(options.title, options.narrative);
  for (const file of options.files) {
    options.onStep?.(`Uploading ${file.name}`);
    await uploadAttachment(record.case_id, file);
  }
  return runExistingV2Pipeline(record.case_id, options.onStep);
}
