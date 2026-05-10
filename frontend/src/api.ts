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
    evidence: Array<{evidence_id: string; type: string; content: string; status: string}>;
    legal_issues: Array<{issue_id: string; title: string; description: string}>;
    citations: Array<{citation_id: string; article: string; title: string; retrieval_score: number}>;
  } | null;
};

export type PipelineResult = {
  caseId: string;
  uiState: V2UiState;
  html?: string;
  htmlPath?: string;
  markdownPath?: string;
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
