import {useEffect, useMemo, useState} from 'react';
import {
  AlertTriangle,
  Bell,
  BookOpen,
  Bot,
  Briefcase,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  FileDown,
  FileText,
  Loader2,
  Maximize2,
  Moon,
  MoreVertical,
  Pause,
  Play,
  RefreshCw,
  Save,
  Scale,
  Scale3d,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Sun,
  UserCheck,
  Upload,
  X,
} from 'lucide-react';

import {
  AuditTrailResponse,
  CaseDetail,
  CaseRecord,
  CourtroomTurn,
  ReportResponse,
  ReviewResponse,
  SimulationResponse,
  V2UiState,
  V1ChallengesResponse,
  V1HearingSession,
  V1OutcomeResponse,
  V1VerificationResponse,
  advanceV1,
  advanceV2,
  createCase,
  exportMvpMarkdown,
  exportV1Html,
  exportV1Markdown,
  exportV2Html,
  exportV2Markdown,
  getAuditTrail,
  getCase,
  getReport,
  getV1Challenges,
  getV1Hearing,
  getV1Outcome,
  getV1Verification,
  getV2UiState,
  healthCheck,
  listCases,
  parseCase,
  reviewCase,
  runExistingV2Pipeline,
  simulateCase,
  startV1,
  startV2,
  uploadAttachment,
} from './api';
import {Avatar, AvatarFallback, AvatarImage} from '@/components/ui/avatar';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Card} from '@/components/ui/card';
import {Collapsible, CollapsibleContent, CollapsibleTrigger} from '@/components/ui/collapsible';
import {ScrollArea} from '@/components/ui/scroll-area';
import {Separator} from '@/components/ui/separator';

const stageLabels: Record<string, string> = {
  opening: 'Mở phiên',
  evidence_presentation: 'Trình bày chứng cứ',
  legal_retrieval: 'Truy xuất pháp luật',
  plaintiff_argument: 'Nguyên đơn tranh luận',
  defense_argument: 'Bị đơn đối đáp',
  evidence_challenge: 'Thách thức chứng cứ',
  judge_questions: 'HĐXX hỏi',
  party_responses: 'Các bên phản hồi',
  fact_check: 'Kiểm chứng sự kiện',
  citation_verification: 'Xác minh viện dẫn',
  preliminary_assessment: 'Nhận định sơ bộ',
  human_review: 'Rà soát con người',
  closing_record: 'Kết thúc phiên',
  case_preparation: 'Chuẩn bị hồ sơ',
  opening_formalities: 'Mở phiên',
  appearance_check: 'Kiểm tra sự có mặt',
  procedure_explanation: 'Phổ biến thủ tục',
  plaintiff_claim_statement: 'Nguyên đơn trình bày',
  defense_response_statement: 'Bị đơn đối đáp',
  evidence_examination: 'Xem xét chứng cứ',
  judge_examination: 'HĐXX hỏi',
  plaintiff_debate: 'Tranh luận',
  defense_rebuttal: 'Đối đáp',
  final_statements: 'Lời sau cùng',
  deliberation: 'Nghị án mô phỏng',
  simulated_decision: 'Kết quả mô phỏng',
};

const statusLabels: Record<string, string> = {
  draft: 'Bản nháp',
  parsed: 'Đã phân tích',
  simulated: 'Đã mô phỏng',
  review_required: 'Cần rà soát',
  report_ready: 'Sẵn sàng báo cáo',
  ok: 'Ổn',
  needs_fact_check: 'Cần kiểm chứng',
  needs_review: 'Cần rà soát',
  rejected: 'Bị loại',
  completed: 'Hoàn tất',
  pending: 'Chờ xử lý',
};

const speakerColors: Record<string, string> = {
  plaintiff_agent: 'blue',
  defense_agent: 'amber',
  judge_agent: 'purple',
  clerk_agent: 'slate',
  evidence_agent: 'emerald',
  legal_retrieval_agent: 'red',
  fact_check_agent: 'orange',
  citation_verifier_agent: 'green',
};

function labelStage(stage?: string) {
  if (!stage) return 'Chưa khởi động';
  return stageLabels[stage] ?? stage.replaceAll('_', ' ');
}

function labelStatus(status?: string) {
  if (!status) return 'Chưa có dữ liệu';
  return statusLabels[status] ?? status.replaceAll('_', ' ');
}

function badgeVariant(status?: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (!status) return 'outline';
  if (status === 'report_ready' || status === 'ok' || status === 'completed') return 'secondary';
  if (status.includes('review') || status.includes('blocked') || status.includes('rejected')) return 'destructive';
  return 'outline';
}

function initials(label: string) {
  return label
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}

function turnTime(index: number) {
  const totalMinutes = 9 * 60 + index * 5;
  const hour = Math.floor(totalMinutes / 60).toString().padStart(2, '0');
  const minute = (totalMinutes % 60).toString().padStart(2, '0');
  return `${hour}:${minute}`;
}

function getCaseTitle(caseDetail: CaseDetail | null, selectedCase: CaseRecord | undefined) {
  return caseDetail?.record.title || selectedCase?.title || 'Chưa chọn hồ sơ';
}

function escapeHtml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

type AppMode = 'mvp' | 'v1' | 'v2';

export default function App() {
  const [activeMode, setActiveMode] = useState<AppMode>('v2');
  const [apiOnline, setApiOnline] = useState(false);
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [newCaseTitle, setNewCaseTitle] = useState('Tranh chấp hợp đồng mua bán xe máy');
  const [newCaseNarrative, setNewCaseNarrative] = useState('Nguyên đơn cho rằng bị đơn vi phạm nghĩa vụ giao tài sản đúng hạn; các bên tranh chấp về điều kiện thanh toán còn lại, hoàn trả tiền đã nhận và chi phí phát sinh.');
  const [files, setFiles] = useState<File[]>([]);
  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [auditTrail, setAuditTrail] = useState<AuditTrailResponse | null>(null);
  const [mvpReport, setMvpReport] = useState<ReportResponse | null>(null);
  const [reviewResult, setReviewResult] = useState<ReviewResponse | null>(null);
  const [v1Session, setV1Session] = useState<V1HearingSession | null>(null);
  const [v1Challenges, setV1Challenges] = useState<V1ChallengesResponse | null>(null);
  const [v1Verification, setV1Verification] = useState<V1VerificationResponse | null>(null);
  const [v1Outcome, setV1Outcome] = useState<V1OutcomeResponse | null>(null);
  const [uiState, setUiState] = useState<V2UiState | null>(null);
  const [htmlPreview, setHtmlPreview] = useState('');
  const [markdownPath, setMarkdownPath] = useState('');
  const [htmlPath, setHtmlPath] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [busyAction, setBusyAction] = useState('');
  const [error, setError] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isLeftSidebarOpen, setIsLeftSidebarOpen] = useState(true);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true);
  const [showPreview, setShowPreview] = useState(false);
  const [showReportBar, setShowReportBar] = useState(true);
  const [showJudgeModal, setShowJudgeModal] = useState(false);

  const selectedCase = useMemo(
    () => cases.find((item) => item.case_id === selectedCaseId),
    [cases, selectedCaseId],
  );

  const parsed = caseDetail?.parsed_case;
  const facts = parsed?.facts ?? [];
  const evidence = parsed?.evidence ?? [];
  const legalIssues = parsed?.legal_issues ?? [];
  const claims = parsed?.claims ?? [];
  const citations = parsed?.citations ?? [];
  const v2Transcript = uiState?.transcript ?? [];
  const v1Transcript: CourtroomTurn[] = (v1Session?.turns ?? []).map((turn) => ({
    turn_id: turn.turn_id,
    trial_stage: turn.hearing_stage,
    speaker: turn.agent,
    speaker_label: labelStage(turn.agent),
    utterance: turn.message,
    claim_ids: turn.claims,
    evidence_ids: turn.evidence_used,
    citation_ids: turn.citations_used,
    status: turn.status,
    risk_notes: [],
  }));
  const mvpTranscript: CourtroomTurn[] = simulation
    ? [
        {
          turn_id: 'MVP_SUMMARY',
          trial_stage: 'simulated',
          speaker: 'judge_agent',
          speaker_label: 'Judge summary',
          utterance: simulation.judge_summary.summary,
          claim_ids: [],
          evidence_ids: [],
          citation_ids: [],
          status: simulation.human_review.blocked ? 'needs_review' : 'ok',
          risk_notes: simulation.judge_summary.unsupported_claims,
        },
        {
          turn_id: 'MVP_REPORT',
          trial_stage: 'report_ready',
          speaker: 'clerk_agent',
          speaker_label: 'Clerk report',
          utterance: simulation.final_report.case_summary,
          claim_ids: [],
          evidence_ids: [],
          citation_ids: [],
          status: simulation.case.status,
          risk_notes: simulation.final_report.human_review_checklist,
        },
      ]
    : [];
  const transcript = activeMode === 'v1' ? v1Transcript : activeMode === 'mvp' ? mvpTranscript : v2Transcript;
  const v2Timeline = uiState?.timeline ?? [];
  const v1Timeline = (v1Session?.stage_order ?? []).map((stage) => ({
    trial_stage: stage,
    label: labelStage(stage),
    status: (v1Session?.turns ?? []).some((turn) => turn.hearing_stage === stage) ? 'completed' : 'pending',
    turn_ids: (v1Session?.turns ?? []).filter((turn) => turn.hearing_stage === stage).map((turn) => turn.turn_id),
  }));
  const mvpTimeline = [
    {trial_stage: 'draft', label: 'Draft', status: caseDetail ? 'completed' : 'pending', turn_ids: []},
    {trial_stage: 'parsed', label: 'Parsed', status: parsed ? 'completed' : 'pending', turn_ids: []},
    {trial_stage: 'simulated', label: 'Simulated', status: simulation ? 'completed' : 'pending', turn_ids: simulation?.trial_minutes.turn_ids ?? []},
    {
      trial_stage: 'review_required',
      label: 'Review',
      status: reviewResult || simulation?.human_review.required ? 'completed' : 'pending',
      turn_ids: [],
    },
    {trial_stage: 'report_ready', label: 'Report', status: mvpReport || reviewResult ? 'completed' : 'pending', turn_ids: []},
  ];
  const timeline = activeMode === 'v1' ? v1Timeline : activeMode === 'mvp' ? mvpTimeline : v2Timeline;
  const currentStage = activeMode === 'v1' ? v1Session?.current_stage : activeMode === 'mvp' ? selectedCase?.status : uiState?.current_stage;
  const currentStageIndex = Math.max(
    0,
    timeline.findIndex((item) => item.trial_stage === currentStage),
  );
  const latestTurn = transcript[transcript.length - 1];
  const reviewCount =
    (uiState?.human_review.checklist.length ?? 0) +
    (uiState?.dialogue_quality.ungrounded_turn_ids.length ?? 0) +
    (uiState?.decision_guard?.unresolved_items.length ?? 0) +
    (simulation?.human_review.checklist.length ?? 0) +
    (v1Session?.human_review.checklist.length ?? 0);
  const okTurns = transcript.filter((turn) => turn.status === 'ok').length;
  const needsReviewTurns = transcript.filter((turn) => turn.status !== 'ok').length;
  const title = getCaseTitle(caseDetail, selectedCase);
  const timelineItems = timeline.length ? timeline : [{trial_stage: 'case_preparation', label: 'Case preparation', status: 'pending', turn_ids: []}];
  const judgeSummaryItems = (
    activeMode === 'v2'
      ? (uiState?.deliberation?.established_facts ?? facts.slice(0, 3).map((fact) => fact.content))
      : activeMode === 'v1'
        ? (v1Outcome?.preliminary_assessment_turns.map((turn) => turn.message) ?? facts.slice(0, 3).map((fact) => fact.content))
        : (simulation?.judge_summary.main_disputed_points ?? facts.slice(0, 3).map((fact) => fact.content))
  ).slice(0, 3);
  const judgeRiskItems = (
    activeMode === 'v2'
      ? (uiState?.decision_guard?.unresolved_items ?? uiState?.human_review.checklist ?? [])
      : activeMode === 'v1'
        ? (v1Session?.human_review.checklist ?? [])
        : (simulation?.human_review.checklist ?? [])
  ).slice(0, 3);
  const judgeNote =
    activeMode === 'v2'
      ? uiState?.simulated_decision?.summary || latestTurn?.utterance || ''
      : activeMode === 'v1'
        ? v1Outcome?.outcome_candidates[0]?.rationale || latestTurn?.utterance || ''
        : simulation?.final_report.case_summary || latestTurn?.utterance || '';
  const modeStatus = activeMode === 'v2' ? uiState?.status || selectedCase?.status : activeMode === 'v1' ? v1Session?.status || selectedCase?.status : simulation?.case.status || selectedCase?.status;

  async function refreshCases(preferredCaseId?: string) {
    setError('');
    const [online, records] = await Promise.all([healthCheck(), listCases()]);
    setApiOnline(online);
    setCases(records);
    const nextCaseId = preferredCaseId || selectedCaseId || records[0]?.case_id || '';
    setSelectedCaseId(nextCaseId);
    if (nextCaseId) {
      await loadCase(nextCaseId, false);
    }
  }

  async function loadCase(caseId: string, showErrors = true) {
    if (!caseId) return;
    setError('');
    setHtmlPreview('');
    setMarkdownPath('');
    setHtmlPath('');
    setSimulation(null);
    setAuditTrail(null);
    setMvpReport(null);
    setReviewResult(null);
    setV1Session(null);
    setV1Challenges(null);
    setV1Verification(null);
    setV1Outcome(null);
    const detail = await getCase(caseId);
    setCaseDetail(detail);
    await Promise.all([
      getAuditTrail(caseId).then(setAuditTrail).catch(() => undefined),
      getReport(caseId).then(setMvpReport).catch(() => undefined),
      getV1Hearing(caseId).then(setV1Session).catch(() => undefined),
      getV1Challenges(caseId).then(setV1Challenges).catch(() => undefined),
      getV1Verification(caseId).then(setV1Verification).catch(() => undefined),
      getV1Outcome(caseId).then(setV1Outcome).catch(() => undefined),
    ]);
    try {
      const state = await getV2UiState(caseId);
      setUiState(state);
    } catch (exc) {
      setUiState(null);
      if (showErrors) {
        setError(exc instanceof Error ? exc.message : String(exc));
      }
    }
  }

  useEffect(() => {
    if (document.documentElement.classList.contains('dark')) {
      setIsDarkMode(true);
    }
    refreshCases().catch((exc) => {
      setError(exc instanceof Error ? exc.message : String(exc));
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function toggleDarkMode() {
    document.documentElement.classList.toggle('dark');
    setIsDarkMode(document.documentElement.classList.contains('dark'));
  }

  async function runAction(action: string, callback: () => Promise<void>) {
    setBusyAction(action);
    setError('');
    try {
      await callback();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusyAction('');
    }
  }

  async function parseSelectedCase() {
    if (!selectedCaseId) return;
    await runAction('parse', async () => {
      setLogs((current) => [...current, 'Phân tích hồ sơ và trích xuất fact/evidence/citation']);
      await parseCase(selectedCaseId);
      await loadCase(selectedCaseId, false);
    });
  }

  async function createCaseFromUi() {
    await runAction('create', async () => {
      setLogs((current) => [...current, 'Tạo hồ sơ mới từ UI']);
      const record = await createCase(newCaseTitle, newCaseNarrative);
      for (const file of files) {
        setLogs((current) => [...current, `Upload attachment: ${file.name}`]);
        await uploadAttachment(record.case_id, file);
      }
      setFiles([]);
      await refreshCases(record.case_id);
      setActiveMode('mvp');
    });
  }

  async function uploadFilesToSelectedCase() {
    if (!selectedCaseId || files.length === 0) return;
    await runAction('upload', async () => {
      for (const file of files) {
        setLogs((current) => [...current, `Upload attachment: ${file.name}`]);
        await uploadAttachment(selectedCaseId, file);
      }
      setFiles([]);
      await loadCase(selectedCaseId, false);
      await refreshCases(selectedCaseId);
    });
  }

  async function runMvpSimulation() {
    if (!selectedCaseId) return;
    await runAction('simulate', async () => {
      setLogs((current) => [...current, 'Chạy MVP simulation']);
      await parseCase(selectedCaseId);
      const result = await simulateCase(selectedCaseId);
      await refreshCases(selectedCaseId);
      setSimulation(result);
      setAuditTrail({case_id: selectedCaseId, audit_trail: result.audit_trail, human_review: result.human_review});
    });
  }

  async function approveMvpReview() {
    if (!selectedCaseId) return;
    await runAction('review', async () => {
      const result = await reviewCase({
        caseId: selectedCaseId,
        decision: 'approve',
        reviewerName: 'Nguyễn Văn A',
        notes: 'Approved from frontend demo review panel.',
      });
      setLogs((current) => [...current, `Human review approved: ${result.report_status}`]);
      await refreshCases(selectedCaseId);
      setReviewResult(result);
      setMvpReport({case_id: result.case_id, report_status: result.report_status, generated_from_turns: [], report: result.report});
    });
  }

  async function startSelectedV1() {
    if (!selectedCaseId) return;
    await runAction('v1-start', async () => {
      setLogs((current) => [...current, 'Khởi động V1 hearing']);
      await parseCase(selectedCaseId);
      const session = await startV1(selectedCaseId);
      setV1Session(session);
      await loadV1Panels(selectedCaseId);
      await refreshCases(selectedCaseId);
    });
  }

  async function advanceSelectedV1() {
    if (!selectedCaseId) return;
    await runAction('v1-advance', async () => {
      setLogs((current) => [...current, `Advance V1 từ stage: ${labelStage(v1Session?.current_stage)}`]);
      const session = await advanceV1(selectedCaseId);
      setV1Session(session);
      await loadV1Panels(selectedCaseId);
      await refreshCases(selectedCaseId);
    });
  }

  async function runFullV1() {
    if (!selectedCaseId) return;
    await runAction('v1-full', async () => {
      setLogs([]);
      setHtmlPreview('');
      await parseCase(selectedCaseId);
      let session = await startV1(selectedCaseId);
      for (let index = 0; index < 20 && session.current_stage !== 'closing_record'; index += 1) {
        setLogs((current) => [...current, `V1 advance ${index + 1}: ${labelStage(session.current_stage)}`]);
        session = await advanceV1(selectedCaseId);
      }
      setV1Session(session);
      await loadV1Panels(selectedCaseId);
      const markdown = await exportV1Markdown(selectedCaseId);
      const html = await exportV1Html(selectedCaseId);
      setMarkdownPath(markdown);
      setHtmlPath(html.htmlPath);
      setHtmlPreview(html.html);
      setShowPreview(true);
      await refreshCases(selectedCaseId);
    });
  }

  async function loadV1Panels(caseId: string) {
    const [challenges, verification, outcome] = await Promise.all([
      getV1Challenges(caseId).catch(() => null),
      getV1Verification(caseId).catch(() => null),
      getV1Outcome(caseId).catch(() => null),
    ]);
    setV1Challenges(challenges);
    setV1Verification(verification);
    setV1Outcome(outcome);
  }

  async function startSelectedV2() {
    if (!selectedCaseId) return;
    await runAction('start', async () => {
      setLogs((current) => [...current, 'Khởi động phiên tòa mô phỏng V2']);
      await startV2(selectedCaseId);
      const state = await getV2UiState(selectedCaseId);
      setUiState(state);
      await refreshCases(selectedCaseId);
    });
  }

  async function advanceSelectedV2() {
    if (!selectedCaseId) return;
    await runAction('advance', async () => {
      setLogs((current) => [...current, `Advance từ stage: ${labelStage(uiState?.current_stage)}`]);
      const state = await advanceV2(selectedCaseId);
      setUiState(state);
      await refreshCases(selectedCaseId);
    });
  }

  async function runFullV2() {
    if (!selectedCaseId) return;
    await runAction('full', async () => {
      setLogs([]);
      setHtmlPreview('');
      const result = await runExistingV2Pipeline(selectedCaseId, (message) => {
        setLogs((current) => [...current, message]);
      });
      setUiState(result.uiState);
      setMarkdownPath(result.markdownPath || '');
      setHtmlPath(result.htmlPath || '');
      setHtmlPreview(result.html || '');
      setShowPreview(Boolean(result.html));
      await refreshCases(selectedCaseId);
    });
  }

  function runFullActiveMode() {
    if (activeMode === 'mvp') {
      return runMvpSimulation();
    }
    if (activeMode === 'v1') {
      return runFullV1();
    }
    return runFullV2();
  }

  function advanceActiveMode() {
    if (activeMode === 'v1') {
      return advanceSelectedV1();
    }
    if (activeMode === 'mvp') {
      return runMvpSimulation();
    }
    return advanceSelectedV2();
  }

  async function exportMarkdown() {
    if (!selectedCaseId) return;
    await runAction('markdown', async () => {
      if (activeMode === 'mvp') {
        const result = await exportMvpMarkdown(selectedCaseId);
        setMarkdownPath(result.markdownPath);
        setHtmlPreview(`<pre>${escapeHtml(result.markdown)}</pre>`);
        setShowPreview(true);
        setLogs((current) => [...current, `Đã xuất MVP Markdown: ${result.markdownPath}`]);
        return;
      }
      const path = activeMode === 'v1' ? await exportV1Markdown(selectedCaseId) : await exportV2Markdown(selectedCaseId);
      setMarkdownPath(path);
      setLogs((current) => [...current, `Đã xuất Markdown: ${path}`]);
    });
  }

  async function exportHtml() {
    if (!selectedCaseId) return;
    await runAction('html', async () => {
      if (activeMode === 'mvp') {
        const result = await exportMvpMarkdown(selectedCaseId);
        setMarkdownPath(result.markdownPath);
        setHtmlPath('');
        setHtmlPreview(`<pre>${escapeHtml(result.markdown)}</pre>`);
        setShowPreview(true);
        setLogs((current) => [...current, `Đã mở MVP Markdown preview: ${result.markdownPath}`]);
        return;
      }
      const result = activeMode === 'v1' ? await exportV1Html(selectedCaseId) : await exportV2Html(selectedCaseId);
      setHtmlPath(result.htmlPath);
      setHtmlPreview(result.html);
      setShowPreview(true);
      setLogs((current) => [...current, `Đã xuất HTML: ${result.htmlPath}`]);
    });
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
      <header className="relative z-10 flex h-16 shrink-0 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur">
        <div className="flex min-w-0 items-center gap-4">
          <div className="flex shrink-0 items-center gap-3 pl-2 font-serif font-bold uppercase leading-[1.1] tracking-widest text-primary">
            <Scale3d className="h-9 w-9" />
            <div className="flex flex-col pt-1">
              <span className="text-xl">AI Courtroom</span>
              <span className="font-sans text-[12px] tracking-[0.4em] text-primary/70">Harness</span>
            </div>
          </div>
          <Separator orientation="vertical" className="mx-4 h-8" />
          <div className="flex shrink-0 rounded-md border border-border bg-muted/40 p-0.5">
            {(['mvp', 'v1', 'v2'] as AppMode[]).map((mode) => (
              <Button
                key={mode}
                variant="ghost"
                size="sm"
                className={`h-8 px-3 text-xs font-semibold uppercase tracking-wide ${activeMode === mode ? 'bg-background text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                onClick={() => setActiveMode(mode)}
              >
                {mode.toUpperCase()}
              </Button>
            ))}
          </div>
          <Separator orientation="vertical" className="mx-2 h-8" />
          <div className="flex min-w-0 flex-col">
            <h1 className="truncate text-sm font-semibold">{title}</h1>
            <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
              <span>{selectedCaseId || 'Chưa chọn case'}</span>
              <Badge variant={badgeVariant(modeStatus)} className="h-5 border border-border/50 bg-muted font-normal text-muted-foreground hover:bg-muted">
                {labelStatus(modeStatus)}
              </Badge>
              <Badge variant={apiOnline ? 'secondary' : 'destructive'} className="h-5">
                {apiOnline ? 'API online' : 'API offline'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <Button variant="outline" size="sm" className="h-9 gap-2 border-border/50 bg-background font-normal text-muted-foreground hover:bg-accent/50" disabled={Boolean(busyAction)} onClick={() => refreshCases(selectedCaseId)}>
            <RefreshCw className={`h-4 w-4 ${busyAction ? 'animate-spin' : ''}`} /> Làm mới
          </Button>
          <Button size="sm" className="h-9 gap-2 rounded border-none bg-primary font-semibold text-primary-foreground hover:bg-primary/90" disabled={!selectedCaseId || Boolean(busyAction)} onClick={runFullActiveMode}>
            {busyAction.includes('full') || busyAction === 'simulate' ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
            {activeMode === 'mvp' ? 'Run MVP' : activeMode === 'v1' ? 'Run V1' : 'Tạo báo cáo'} <ChevronDown className="h-4 w-4 opacity-70" />
          </Button>
          <Button variant="ghost" size="icon" onClick={toggleDarkMode} className="h-9 w-9 text-muted-foreground hover:bg-accent/50">
            {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          <Button variant="ghost" size="icon" className="relative h-9 w-9 text-muted-foreground hover:bg-accent/50">
            <Bell className="h-4 w-4" />
            {reviewCount > 0 && <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full border border-background bg-destructive" />}
          </Button>
          <Separator orientation="vertical" className="mx-1 h-6" />
          <div className="flex items-center gap-3 pl-2">
            <Avatar className="h-8 w-8 ring-1 ring-border/50">
              <AvatarImage src="https://i.pravatar.cc/150?u=a042581f4e29026704d" alt="User" />
              <AvatarFallback className="bg-muted text-xs">NV</AvatarFallback>
            </Avatar>
            <div className="hidden flex-col sm:flex">
              <span className="text-sm font-medium leading-none">Nguyễn Văn A</span>
              <span className="mt-1 text-[10px] text-muted-foreground">Thẩm phán</span>
            </div>
          </div>
        </div>
      </header>

      <div className="relative flex min-h-0 flex-1 overflow-hidden">
        <aside className={`${isLeftSidebarOpen ? 'w-72 border-r' : 'w-0 border-r-0'} relative z-20 flex min-h-0 shrink-0 flex-col border-border bg-card/30 transition-all duration-300`}>
          <div className={`flex h-full min-h-0 w-72 flex-col overflow-hidden transition-opacity duration-300 ${isLeftSidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'}`}>
            <div className="shrink-0 border-b border-border/50 p-3">
              <Button variant="ghost" onClick={() => setIsLeftSidebarOpen(false)} className="h-9 w-full justify-between font-normal text-muted-foreground hover:text-foreground">
                <div className="flex items-center gap-2">
                  <ChevronRight className="h-4 w-4 rotate-180" /> Thu gọn
                </div>
                <ChevronRight className="h-3 w-3 opacity-50" />
              </Button>
            </div>

            <ScrollArea className="min-h-0 flex-1">
              <div className="w-72 space-y-2 p-3">
                <div className="space-y-2 rounded-lg border border-border/50 bg-background p-3">
                  <label className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Hồ sơ từ BE</label>
                  {activeMode === 'mvp' && (
                    <div className="space-y-2 rounded-md border border-dashed border-border p-2">
                      <input
                        className="h-8 w-full rounded-md border border-border bg-background px-2 text-xs outline-none focus:border-primary"
                        value={newCaseTitle}
                        onChange={(event) => setNewCaseTitle(event.target.value)}
                        placeholder="Tên hồ sơ mới"
                      />
                      <textarea
                        className="h-20 w-full resize-none rounded-md border border-border bg-background px-2 py-1.5 text-xs leading-5 outline-none focus:border-primary"
                        value={newCaseNarrative}
                        onChange={(event) => setNewCaseNarrative(event.target.value)}
                        placeholder="Narrative"
                      />
                      <Button className="h-8 w-full gap-2" size="sm" disabled={Boolean(busyAction) || !newCaseTitle || !newCaseNarrative} onClick={createCaseFromUi}>
                        {busyAction === 'create' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                        Tạo case
                      </Button>
                    </div>
                  )}
                  <select
                    className="h-9 w-full rounded-md border border-border bg-background px-2 text-sm outline-none focus:border-primary"
                    value={selectedCaseId}
                    onChange={(event) => {
                      const nextCaseId = event.target.value;
                      setSelectedCaseId(nextCaseId);
                      loadCase(nextCaseId).catch((exc) => setError(exc instanceof Error ? exc.message : String(exc)));
                    }}
                  >
                    <option value="">Chọn hồ sơ</option>
                    {cases.map((item) => (
                      <option key={item.case_id} value={item.case_id}>
                        {item.case_id} - {item.title}
                      </option>
                    ))}
                  </select>
                  <label className="flex h-9 cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-border px-2 text-xs text-muted-foreground hover:bg-muted/50">
                    <Upload className="h-3.5 w-3.5" />
                    {files.length ? `${files.length} file đã chọn` : 'Chọn attachment'}
                    <input className="hidden" type="file" multiple onChange={(event) => setFiles(Array.from(event.target.files || []))} />
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <Button variant="outline" size="sm" className="h-8 gap-1" disabled={!selectedCaseId || Boolean(busyAction)} onClick={parseSelectedCase}>
                      {busyAction === 'parse' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                      Parse
                    </Button>
                    <Button variant="outline" size="sm" className="h-8 gap-1" disabled={!selectedCaseId || files.length === 0 || Boolean(busyAction)} onClick={uploadFilesToSelectedCase}>
                      {busyAction === 'upload' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
                      Upload
                    </Button>
                  </div>
                  {activeMode === 'mvp' && (
                    <Button variant="outline" size="sm" className="h-8 w-full gap-1" disabled={!selectedCaseId || Boolean(busyAction)} onClick={runMvpSimulation}>
                      {busyAction === 'simulate' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                      Simulate MVP
                    </Button>
                  )}
                  {activeMode === 'v1' && (
                    <div className="grid grid-cols-2 gap-2">
                      <Button variant="outline" size="sm" className="h-8 gap-1" disabled={!selectedCaseId || Boolean(busyAction)} onClick={startSelectedV1}>
                        {busyAction === 'v1-start' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                        Start V1
                      </Button>
                      <Button variant="outline" size="sm" className="h-8 gap-1" disabled={!selectedCaseId || Boolean(busyAction)} onClick={advanceSelectedV1}>
                        {busyAction === 'v1-advance' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ChevronRight className="h-3.5 w-3.5" />}
                        Advance
                      </Button>
                    </div>
                  )}
                  {activeMode === 'v2' && (
                    <Button variant="outline" size="sm" className="h-8 w-full gap-1" disabled={!selectedCaseId || Boolean(busyAction)} onClick={startSelectedV2}>
                      {busyAction === 'start' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
                      Start V2
                    </Button>
                  )}
                </div>

                <Collapsible defaultOpen>
                  <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md p-2 text-sm font-medium hover:bg-accent">
                    <div className="flex items-center gap-2 text-primary">
                      <FileText className="h-4 w-4" />
                      <span className="text-xs font-semibold uppercase tracking-wide">Tóm tắt vụ án</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <span className="rounded-sm bg-muted px-1.5 py-0.5 text-xs">{facts.length}</span>
                      <ChevronDown className="h-3 w-3" />
                    </div>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="space-y-3 px-2 pb-4 pt-2">
                    <InfoPair label="Loại" value={caseDetail?.record.case_type.replaceAll('_', ' ') || 'Chưa có'} />
                    <InfoPair label="Ngôn ngữ" value={caseDetail?.record.language || 'vi'} />
                    <InfoPair label="Đính kèm" value={`${caseDetail?.record.attachment_count ?? 0} file`} />
                    <Separator className="bg-border/50" />
                    <div className="space-y-2">
                      <span className="text-sm text-muted-foreground">Narrative</span>
                      <p className="line-clamp-5 text-sm leading-6 text-foreground">{caseDetail?.case_input.narrative || 'Chưa có mô tả hồ sơ.'}</p>
                    </div>
                    <Button variant="outline" size="sm" className="mt-2 w-full border-border/50" disabled={!selectedCaseId} onClick={() => loadCase(selectedCaseId)}>
                      Xem dữ liệu mới nhất
                    </Button>
                  </CollapsibleContent>
                </Collapsible>

                <Separator className="my-2 bg-border/30" />
                <MiniSection icon={Scale} title="Chứng cứ" count={evidence.length} items={evidence.map((item) => `${item.evidence_id}: ${item.content}`)} />
                <MiniSection icon={BookOpen} title="Vấn đề pháp lý" count={legalIssues.length} items={legalIssues.map((item) => item.title)} />
                <MiniSection icon={ShieldAlert} title="Fact đã trích xuất" count={facts.length} items={facts.map((item) => item.content)} />

                <Card className="border-border/50 bg-background p-3 shadow-sm">
                  <div className="mb-3 flex items-center gap-2 text-primary">
                    <Bot className="h-4 w-4" />
                    <span className="text-xs font-semibold uppercase tracking-wide">Run log</span>
                  </div>
                  <div className="space-y-2 text-xs leading-5 text-muted-foreground">
                    {logs.slice(-5).map((item, index) => (
                      <div key={`${item}-${index}`} className="flex gap-2">
                        <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                        <span>{item}</span>
                      </div>
                    ))}
                    {logs.length === 0 && <p>Chưa chạy thao tác nào trong phiên này.</p>}
                  </div>
                </Card>
              </div>
            </ScrollArea>

            <div className="grid shrink-0 grid-cols-4 gap-1 border-t border-border/50 bg-background/50 p-2">
              <SidebarNav icon={Briefcase} label="Hồ sơ" active />
              <SidebarNav icon={BookOpen} label="Thư viện" />
              <SidebarNav icon={Bot} label="Trợ lý AI" />
              <SidebarNav icon={Settings} label="Cài đặt" />
            </div>
          </div>

          {!isLeftSidebarOpen && (
            <Button variant="outline" size="icon" onClick={() => setIsLeftSidebarOpen(true)} className="absolute -right-3 top-3 z-50 h-8 w-8 translate-x-full rounded-full border-border bg-background shadow-md hover:bg-muted sm:-right-4">
              <ChevronRight className="h-4 w-4" />
            </Button>
          )}
        </aside>

        <main className={`relative flex min-h-0 min-w-0 flex-1 flex-col bg-background p-4 ${showReportBar ? 'pb-20' : 'pb-4'}`}>
          <Card className="relative z-10 flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border-none shadow-xl">
            <div className="absolute inset-0 z-0 bg-background" />
            <div className="relative z-10 flex items-center justify-between border-b border-border bg-muted/30 p-4 text-foreground">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded bg-primary/10 text-primary">
                  <Scale3d className="h-5 w-5" />
                </div>
                <h2 className="truncate font-serif text-lg font-bold uppercase tracking-wide text-foreground">
                  Biên bản phiên tòa
                  <span className="relative top-[-2px] ml-2 rounded-full bg-primary/10 px-2 py-0.5 pb-[3px] font-sans text-[10px] font-medium uppercase tracking-normal text-primary">
                    {activeMode.toUpperCase()} từ backend
                  </span>
                </h2>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="h-8 border-border bg-background/50 text-xs font-medium hover:bg-muted" disabled={!selectedCaseId || Boolean(busyAction)} onClick={advanceActiveMode}>
                  {busyAction === 'advance' || busyAction === 'v1-advance' || busyAction === 'simulate' ? <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> : <Play className="mr-2 h-3.5 w-3.5" />}
                  {activeMode === 'mvp' ? 'Simulate' : 'Advance stage'}
                </Button>
                <Button variant="outline" size="icon" className="h-8 w-8 border-border bg-background/50 hover:bg-muted" onClick={() => setShowPreview((current) => !current)} disabled={!htmlPreview}>
                  <Maximize2 className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="relative z-10 h-[112px] select-none overflow-x-auto border-b border-border text-foreground [scrollbar-width:thin] [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-border [&::-webkit-scrollbar-track]:bg-transparent">
              <div className="relative flex h-full min-w-max px-5">
                {timelineItems.map((item, index) => {
                  const active = item.trial_stage === uiState?.current_stage;
                  const completed = item.status === 'completed';
                  const past = index <= currentStageIndex;
                  return (
                    <div className="relative flex h-full w-40 shrink-0 flex-col items-center px-3 pt-2" key={item.trial_stage}>
                      <div className={`${past ? 'bg-primary/70' : 'bg-border'} absolute left-0 right-0 top-[47px] z-0 h-px ${index === 0 ? 'left-1/2' : ''} ${index === timelineItems.length - 1 ? 'right-1/2' : ''}`} />
                      {active && <div className="absolute inset-x-2 bottom-0 top-[3px] z-0 rounded-t-md bg-primary/5 ring-1 ring-primary/10" />}
                      <span className={`${active ? 'border-primary/30 bg-primary/10 text-primary' : 'border-border bg-background text-muted-foreground'} relative z-10 mb-1 flex h-5 min-w-12 items-center justify-center rounded-full border px-1.5 text-[10px] font-medium shadow-sm`}>
                        {item.turn_ids.length} lượt
                      </span>
                      <div className="relative z-10 flex h-10 items-center justify-center">
                        <div className={`${completed ? 'border-primary bg-primary text-primary-foreground' : active ? 'border-primary bg-background text-primary' : 'border-border bg-background text-muted-foreground'} flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-bold shadow-sm`}>
                          {index + 1}
                        </div>
                      </div>
                      <span className={`${active ? 'text-primary' : 'text-foreground'} relative z-10 mt-1.5 line-clamp-2 min-h-8 text-center text-[11px] font-semibold uppercase leading-4 tracking-wide`}>
                        {labelStage(item.trial_stage)}
                      </span>
                      <span className="relative z-10 mt-1 text-[10px] uppercase tracking-wide text-muted-foreground">{labelStatus(item.status)}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <ScrollArea className="relative z-10 min-h-0 flex-1 p-6 px-10">
              <div className="absolute bottom-6 left-[83px] top-8 w-px bg-border" />
              <div className="relative z-10 mx-auto max-w-4xl space-y-8">
                {transcript.map((turn, index) => (
                  <div key={turn.turn_id}>
                    <TranscriptItem turn={turn} index={index} />
                  </div>
                ))}
                {transcript.length === 0 && (
                  <div className="rounded-lg border border-dashed border-border bg-muted/30 p-8 text-center">
                    <Scale className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
                    <p className="font-medium">Chưa có biên bản V2 cho hồ sơ này.</p>
                    <p className="mt-1 text-sm text-muted-foreground">Bấm Parse, Start V2 hoặc Tạo báo cáo để lấy dữ liệu thật từ backend.</p>
                  </div>
                )}
              </div>
            </ScrollArea>

            <div className="relative z-20 m-0 overflow-hidden rounded-b-xl border-t border-border bg-muted/50 p-2.5">
              <div className="absolute left-0 right-0 top-0 h-5 bg-gradient-to-b from-primary/5 to-transparent" />
              <div className="relative z-10 mb-2 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Scale className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-primary">Nhận định của Thẩm phán</h3>
                </div>
                <Button variant="outline" size="sm" className="h-8 gap-2 border-border bg-background" onClick={() => setShowJudgeModal(true)}>
                  <Maximize2 className="h-3.5 w-3.5" />
                  Mở rộng
                </Button>
              </div>
              <div className="relative z-10 mb-2 grid grid-cols-[1fr_1fr_1.4fr] gap-2">
                <CompactJudgeCard title="Tóm tắt" value={judgeSummaryItems[0] || 'Chưa có sự kiện đã xác lập.'} />
                <CompactJudgeCard title="Điểm mở" value={judgeRiskItems[0] || 'Chưa có cờ rủi ro nổi bật.'} muted />
                <CompactJudgeCard title="Kết quả mô phỏng" value={judgeNote || 'Chờ dữ liệu từ BE v2.'} accent />
              </div>
              <div className="relative z-10 flex gap-2">
                <Button className="h-9 w-[160px] gap-2 border-none bg-primary font-bold text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90" disabled={!selectedCaseId || Boolean(busyAction)} onClick={advanceActiveMode}>
                  {busyAction === 'advance' || busyAction === 'v1-advance' || busyAction === 'simulate' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-current" />} Tiếp tục phiên
                </Button>
                <Button variant="outline" className="h-9 flex-1 gap-2 border-border bg-background font-medium hover:bg-muted">
                  <Pause className="h-4 w-4 fill-current opacity-70" /> Tạm dừng
                </Button>
                <Button variant="outline" className="h-9 flex-1 gap-2 border-border bg-background font-medium hover:bg-muted" disabled={!selectedCaseId || Boolean(busyAction)} onClick={exportHtml}>
                  {busyAction === 'html' ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4 text-primary" />} Xuất HTML
                </Button>
                <Button variant="outline" className="h-9 flex-1 gap-2 border-border bg-background font-medium hover:bg-muted" disabled={!selectedCaseId || Boolean(busyAction)} onClick={runFullActiveMode}>
                  {busyAction.includes('full') || busyAction === 'simulate' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Scale className="h-4 w-4 text-primary" />} Chạy đầy đủ
                </Button>
              </div>
            </div>
          </Card>
        </main>

        <aside className={`${isRightSidebarOpen ? 'w-80 border-l' : 'w-0 border-l-0'} relative z-20 flex min-h-0 shrink-0 flex-col border-border bg-card/30 transition-all duration-300`}>
          <div className={`flex h-full min-h-0 w-80 flex-col overflow-hidden transition-opacity duration-300 ${isRightSidebarOpen ? 'opacity-100' : 'pointer-events-none opacity-0'}`}>
            <div className="shrink-0 border-b border-border/50 p-3">
              <Button variant="ghost" onClick={() => setIsRightSidebarOpen(false)} className="h-9 w-full justify-between font-normal text-muted-foreground hover:text-foreground">
                <div className="flex items-center gap-2">
                  <ChevronRight className="h-4 w-4" /> Thu gọn
                </div>
              </Button>
            </div>

            <ScrollArea className="min-h-0 flex-1">
              <div className="w-80 space-y-3 p-3">
                <Card className="border-border/50 bg-background shadow-sm">
                  <Collapsible defaultOpen className="flex flex-col">
                    <CollapsibleTrigger className="flex w-full items-center justify-between p-3 transition-colors hover:bg-accent/50">
                      <div className="flex items-center gap-2 text-primary">
                        <BookOpen className="h-4 w-4" />
                        <span className="text-xs font-semibold uppercase tracking-wide">Trích dẫn pháp luật</span>
                      </div>
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <span className="rounded-sm bg-muted px-1.5 py-0.5 text-xs">{citations.length}</span>
                        <ChevronDown className="h-3 w-3" />
                      </div>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="space-y-3 p-3 pt-0">
                      {citations.slice(0, 5).map((item) => (
                        <div className="flex gap-3" key={item.citation_id}>
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-red-900/20 bg-red-900/10 text-red-500">
                            <BookOpen className="h-4 w-4" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <h5 className="truncate text-sm font-semibold text-foreground/90">{item.article}</h5>
                            <p className="mb-1 truncate text-xs text-muted-foreground">{item.title}</p>
                            <Badge variant="outline" className="h-4 border-green-500/30 bg-green-500/5 px-1.5 py-0 text-[9px] text-green-600">
                              score {item.retrieval_score.toFixed(2)}
                            </Badge>
                          </div>
                        </div>
                      ))}
                      {citations.length === 0 && <p className="text-sm text-muted-foreground">Chưa có citation từ parsed case.</p>}
                    </CollapsibleContent>
                  </Collapsible>
                </Card>

                <DataPanel
                  icon={Scale}
                  title="Evidence table"
                  count={evidence.length}
                  items={evidence.slice(0, 6).map((item) => ({
                    id: item.evidence_id,
                    title: `${item.type} · ${item.status}`,
                    body: item.content,
                    meta: item.source,
                  }))}
                  empty="Chưa có evidence từ parsed case."
                />

                <DataPanel
                  icon={FileText}
                  title="Claims"
                  count={claims.length}
                  items={claims.slice(0, 6).map((item) => ({
                    id: item.claim_id,
                    title: `${item.speaker} · ${item.confidence}`,
                    body: item.content,
                    meta: [...item.evidence_ids, ...item.citation_ids].join(', '),
                  }))}
                  empty="Chưa có claim từ parser/simulation."
                />

                {activeMode === 'mvp' && (
                  <>
                    <DataPanel
                      icon={ShieldAlert}
                      title="Audit trail"
                      count={auditTrail?.audit_trail.length ?? simulation?.audit_trail.length ?? 0}
                      items={(auditTrail?.audit_trail ?? simulation?.audit_trail ?? []).slice(0, 5).map((item) => ({
                        id: item.event_id,
                        title: `${item.stage} · ${item.severity}`,
                        body: item.message,
                      }))}
                      empty="Chạy simulation để có audit trail."
                    />
                    <Card className="border-border/50 bg-background p-4 shadow-sm">
                      <div className="mb-3 flex items-center gap-2 text-primary">
                        <UserCheck className="h-4 w-4" />
                        <span className="text-xs font-semibold uppercase tracking-wide">Human review</span>
                      </div>
                      <div className="space-y-2 text-sm text-muted-foreground">
                        <InfoLine label="Required" value={String(simulation?.human_review.required ?? false)} />
                        <InfoLine label="Blocked" value={String(simulation?.human_review.blocked ?? false)} />
                        {(simulation?.human_review.checklist ?? []).slice(0, 3).map((item) => (
                          <p className="rounded-md bg-muted/50 p-2 text-xs leading-5" key={item}>{item}</p>
                        ))}
                        {reviewResult && <Badge variant="secondary">{reviewResult.report_status}</Badge>}
                      </div>
                      <Button className="mt-3 h-8 w-full gap-2" size="sm" disabled={!selectedCaseId || Boolean(busyAction) || !simulation} onClick={approveMvpReview}>
                        {busyAction === 'review' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                        Approve review
                      </Button>
                    </Card>
                  </>
                )}

                {activeMode === 'v1' && (
                  <>
                    <DataPanel
                      icon={ShieldAlert}
                      title="Evidence challenges"
                      count={v1Challenges?.challenges.length ?? v1Session?.evidence_challenges.length ?? 0}
                      items={(v1Challenges?.challenges ?? v1Session?.evidence_challenges ?? []).slice(0, 5).map((item) => ({
                        id: item.challenge_id,
                        title: `${item.evidence_id} · ${item.admissibility}`,
                        body: item.reason,
                        meta: item.raised_by,
                      }))}
                      empty="Start/advance V1 để xem challenge."
                    />
                    <DataPanel
                      icon={ShieldCheck}
                      title="Verification turns"
                      count={v1Verification?.verification_turns.length ?? 0}
                      items={(v1Verification?.verification_turns ?? []).slice(0, 5).map((item) => ({
                        id: item.turn_id,
                        title: `${labelStage(item.agent)} · ${labelStage(item.hearing_stage)}`,
                        body: item.message,
                        meta: item.status,
                      }))}
                      empty="V1 verification chưa có dữ liệu."
                    />
                    <DataPanel
                      icon={BookOpen}
                      title="Clarification"
                      count={(v1Session?.clarification_questions.length ?? 0) + (v1Session?.party_responses.length ?? 0)}
                      items={[
                        ...(v1Session?.clarification_questions ?? []).map((item) => ({
                          id: item.question_id,
                          title: `Question · ${item.status}`,
                          body: item.question,
                          meta: item.target_agents.join(', '),
                        })),
                        ...(v1Session?.party_responses ?? []).map((item) => ({
                          id: item.response_id,
                          title: `Response · ${item.responder}`,
                          body: item.content,
                          meta: item.status,
                        })),
                      ].slice(0, 6)}
                      empty="Chưa có clarification round."
                    />
                  </>
                )}

                {activeMode === 'v2' && (
                  <>
                    <DataPanel
                      icon={ShieldAlert}
                      title="Evidence examination"
                      count={uiState?.evidence_examinations.length ?? 0}
                      items={(uiState?.evidence_examinations ?? []).slice(0, 5).map((item) => ({
                        id: item.examination_id,
                        title: `${item.evidence_id} · ${item.admissibility}`,
                        body: item.notes || item.plaintiff_position,
                        meta: item.defense_position,
                      }))}
                      empty="Chưa có V2 evidence examination."
                    />
                    <DataPanel
                      icon={FileText}
                      title="Debate & final statements"
                      count={(uiState?.debate_rounds?.length ?? 0) + (uiState?.final_statements?.length ?? 0)}
                      items={[
                        ...(uiState?.debate_rounds ?? []).map((item) => ({
                          id: item.debate_id,
                          title: item.topic,
                          body: item.judge_summary,
                          meta: item.unresolved_points.join(', '),
                        })),
                        ...(uiState?.final_statements ?? []).map((item) => ({
                          id: item.statement_id,
                          title: labelStage(item.speaker),
                          body: item.content,
                          meta: item.requested_outcome || '',
                        })),
                      ].slice(0, 5)}
                      empty="Chưa có debate/final statements."
                    />
                  </>
                )}

                <RightToggle icon={ShieldAlert} title="Kiểm toán & Rà soát" count={reviewCount} />
                <RightToggle icon={UserCheck} title="Rà soát của con người" count={activeMode === 'v2' ? (uiState?.human_review.checklist.length ?? 0) : activeMode === 'v1' ? (v1Session?.human_review.checklist.length ?? 0) : (simulation?.human_review.checklist.length ?? 0)} />

                <Card className="border-border/50 bg-background p-4 shadow-sm">
                  <div className="mb-4 flex items-center gap-2 text-primary">
                    <Scale className="h-4 w-4" />
                    <span className="text-xs font-semibold uppercase tracking-wide">Cờ xác minh / Trạng thái</span>
                  </div>
                  <div className="space-y-3 text-sm">
                    <StatusLine label="Đã xác minh" count={okTurns} tone="green" />
                    <StatusLine label="Cần rà soát" count={needsReviewTurns} tone="yellow" strong />
                    <StatusLine label="Ungrounded" count={activeMode === 'v2' ? (uiState?.dialogue_quality.ungrounded_turn_ids.length ?? 0) : 0} tone="zinc" />
                  </div>
                  <Separator className="my-3 bg-border/50" />
                  <div className="flex items-center justify-between text-sm font-semibold">
                    <span>Tổng lượt thoại</span>
                    <span>{transcript.length}</span>
                  </div>
                </Card>

                <Card className="border-border/50 bg-background p-4 shadow-sm">
                  <div className="mb-3 flex items-center gap-2 text-primary">
                    <ShieldCheck className="h-4 w-4" />
                    <span className="text-xs font-semibold uppercase tracking-wide">Kết quả mô phỏng</span>
                  </div>
                  {activeMode === 'v2' && uiState?.simulated_decision ? (
                    <div className="space-y-3 text-sm">
                      <Badge variant={badgeVariant(uiState.simulated_decision.risk_level)}>{uiState.simulated_decision.disposition}</Badge>
                      <p className="leading-6 text-muted-foreground">{uiState.simulated_decision.relief_or_next_step}</p>
                      <ul className="space-y-2 text-xs leading-5 text-muted-foreground">
                        {uiState.simulated_decision.rationale.slice(0, 3).map((item) => (
                          <li className="flex gap-2" key={item}>
                            <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : activeMode === 'v1' && v1Outcome?.outcome_candidates.length ? (
                    <div className="space-y-3 text-sm">
                      <Badge variant={badgeVariant(v1Outcome.outcome_candidates[0].risk_level)}>{v1Outcome.outcome_candidates[0].disposition}</Badge>
                      <p className="leading-6 text-muted-foreground">{v1Outcome.outcome_candidates[0].rationale}</p>
                    </div>
                  ) : activeMode === 'mvp' && (mvpReport || simulation) ? (
                    <div className="space-y-3 text-sm">
                      <Badge variant={badgeVariant(mvpReport?.report_status || simulation?.case.status)}>{labelStatus(mvpReport?.report_status || simulation?.case.status)}</Badge>
                      <p className="leading-6 text-muted-foreground">{mvpReport?.report.case_summary || simulation?.final_report.case_summary}</p>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Kết quả sẽ xuất hiện sau khi chạy mode hiện tại.</p>
                  )}
                </Card>

                {error && (
                  <Card className="border-destructive/30 bg-background p-4 text-sm shadow-sm">
                    <div className="flex gap-2">
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                      <p className="leading-5">{error}</p>
                    </div>
                  </Card>
                )}
              </div>
            </ScrollArea>
          </div>

          {!isRightSidebarOpen && (
            <Button variant="outline" size="icon" onClick={() => setIsRightSidebarOpen(true)} className="absolute -left-3 top-3 h-8 w-8 -translate-x-full rounded-full border-border bg-background shadow-md hover:bg-muted sm:-left-4">
              <ChevronRight className="h-4 w-4 rotate-180" />
            </Button>
          )}
        </aside>

        {showReportBar ? (
        <div className="absolute bottom-4 left-4 right-4 z-20 flex items-center justify-between rounded-lg border border-border bg-background p-3 text-foreground shadow-xl">
          <div className="flex min-w-0 items-center gap-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <span className="text-sm font-semibold uppercase tracking-wide">Xem trước báo cáo</span>
              <Badge variant="secondary" className="ml-1 h-5 border-none bg-blue-500/10 text-[10px] font-medium text-blue-600">
                {htmlPreview ? 'Đã xuất' : 'Bản nháp'}
              </Badge>
            </div>
            <div className="mx-2 h-6 w-px bg-border" />
            <div className="flex items-center gap-2 truncate text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              <ProgressPill done={Boolean(parsed)} label="Thông tin vụ án" index={1} />
              <ProgressBar />
              <ProgressPill done={transcript.length > 0} active={transcript.length > 0 && !judgeNote} label="Diễn biến phiên tòa" index={2} />
              <ProgressBar />
              <ProgressPill done={Boolean(judgeNote)} active={Boolean(judgeNote && activeMode !== 'mvp' && !mvpReport)} label="Nhận định & căn cứ" index={3} />
              <ProgressBar />
              <ProgressPill done={Boolean(uiState?.simulated_decision || v1Outcome?.outcome_candidates.length || mvpReport || reviewResult)} active={Boolean(uiState?.simulated_decision || v1Outcome?.outcome_candidates.length || mvpReport || reviewResult)} label="Quyết định dự thảo" index={4} />
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-3">
            <Button variant="outline" size="sm" className="h-9 gap-2 border-border font-medium hover:bg-muted" disabled={!selectedCaseId || Boolean(busyAction)} onClick={exportMarkdown}>
              Xuất MD <FileDown className="h-4 w-4 text-blue-500" />
            </Button>
            <Button variant="outline" size="sm" className="h-9 gap-2 border-border font-medium hover:bg-muted" disabled={!selectedCaseId || Boolean(busyAction)} onClick={exportHtml}>
              Xuất HTML <FileDown className="h-4 w-4 text-red-500" />
            </Button>
            <Button size="sm" className="ml-2 h-9 gap-2 border border-primary/20 bg-primary/10 font-semibold text-primary hover:bg-primary/20" disabled={!htmlPreview} onClick={() => setShowPreview(true)}>
              Mở đầy đủ <Maximize2 className="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="icon" className="ml-2 h-9 w-9 text-muted-foreground hover:bg-muted hover:text-foreground" onClick={() => {
              setShowPreview(false);
              setShowReportBar(false);
            }}>
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>
        ) : (
          <Button
            variant="outline"
            size="sm"
            className="absolute bottom-4 right-4 z-20 h-9 gap-2 border-border bg-background shadow-xl"
            onClick={() => setShowReportBar(true)}
          >
            <FileText className="h-4 w-4" />
            Báo cáo
          </Button>
        )}

        {showJudgeModal && (
          <div className="absolute inset-6 z-40 overflow-hidden rounded-xl border border-border bg-background shadow-2xl">
            <div className="flex h-12 items-center justify-between border-b px-4">
              <div className="flex min-w-0 items-center gap-2">
                <Scale className="h-4 w-4 text-primary" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold uppercase tracking-wide text-primary">Nhận định của Thẩm phán</p>
                  <p className="truncate text-xs text-muted-foreground">{title}</p>
                </div>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowJudgeModal(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            <ScrollArea className="h-[calc(100%-3rem)]">
              <div className="grid gap-4 p-5 lg:grid-cols-2">
                <JudgePanel title="Tóm tắt tranh tụng" items={judgeSummaryItems} />
                <JudgePanel title="Rủi ro / điểm mở" badge="AI" items={judgeRiskItems} muted />
                <div className="rounded-lg border border-border bg-background p-4 shadow-sm lg:col-span-2">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <h4 className="text-[11px] font-semibold uppercase tracking-wider text-foreground/80">Ghi chú / kết quả mô phỏng</h4>
                    <Badge variant={badgeVariant(uiState?.simulated_decision?.risk_level)}>
                      {uiState?.simulated_decision?.risk_level ? `Risk: ${uiState.simulated_decision.risk_level}` : 'BE v2'}
                    </Badge>
                  </div>
                  <textarea
                    className="h-40 w-full resize-none rounded-lg border border-border bg-muted/30 p-3 text-sm leading-6 text-foreground placeholder:text-muted-foreground focus:border-primary/50 focus:outline-none"
                    value={judgeNote}
                    readOnly
                    placeholder="Kết quả mô phỏng sẽ xuất hiện sau stage simulated_decision..."
                  />
                </div>
                <div className="flex gap-3 lg:col-span-2">
                  <Button className="h-9 w-[180px] gap-2 border-none bg-primary font-bold text-primary-foreground hover:bg-primary/90" disabled={!selectedCaseId || Boolean(busyAction)} onClick={advanceActiveMode}>
                    {busyAction === 'advance' || busyAction === 'v1-advance' || busyAction === 'simulate' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-current" />} Tiếp tục phiên
                  </Button>
                  <Button variant="outline" className="h-9 flex-1 gap-2 border-border bg-background font-medium hover:bg-muted" disabled={!selectedCaseId || Boolean(busyAction)} onClick={exportHtml}>
                    {busyAction === 'html' ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4 text-primary" />} Xuất HTML
                  </Button>
                  <Button variant="outline" className="h-9 flex-1 gap-2 border-border bg-background font-medium hover:bg-muted" disabled={!selectedCaseId || Boolean(busyAction)} onClick={runFullActiveMode}>
                    {busyAction.includes('full') || busyAction === 'simulate' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Scale className="h-4 w-4 text-primary" />} Chạy đầy đủ
                  </Button>
                </div>
              </div>
            </ScrollArea>
          </div>
        )}

        {showPreview && htmlPreview && (
          <div className="absolute inset-6 z-30 rounded-xl border border-border bg-background shadow-2xl">
            <div className="flex h-12 items-center justify-between border-b px-4">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">HTML report preview</p>
                <p className="truncate text-xs text-muted-foreground">{htmlPath || markdownPath}</p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowPreview(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            <iframe className="h-[calc(100%-3rem)] w-full bg-white" srcDoc={htmlPreview} title="V2 report preview" />
          </div>
        )}
      </div>
    </div>
  );
}

function CompactJudgeCard({title, value, muted = false, accent = false}: {title: string; value: string; muted?: boolean; accent?: boolean}) {
  return (
    <div className={`${accent ? 'border-primary/20 bg-primary/5' : 'border-border bg-background'} min-w-0 rounded-md border px-3 py-2 shadow-sm`}>
      <div className="mb-1 flex items-center gap-1.5">
        <CheckCircle2 className={`${muted ? 'text-muted-foreground/50' : accent ? 'text-primary' : 'text-primary'} h-3.5 w-3.5 shrink-0`} />
        <span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{title}</span>
      </div>
      <p className="line-clamp-1 text-xs leading-5 text-foreground/90">{value}</p>
    </div>
  );
}

function InfoLine({label, value}: {label: string; value: string}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border/50 pb-1 last:border-b-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="max-w-[170px] truncate text-right text-xs font-medium text-foreground">{value}</span>
    </div>
  );
}

function DataPanel({
  icon: Icon,
  title,
  count,
  items,
  empty,
}: {
  icon: typeof Scale;
  title: string;
  count: number;
  items: Array<{id: string; title: string; body: string; meta?: string}>;
  empty: string;
}) {
  return (
    <Card className="border-border/50 bg-background shadow-sm">
      <Collapsible>
        <CollapsibleTrigger className="flex w-full items-center justify-between p-3 transition-colors hover:bg-accent/50">
          <div className="flex items-center gap-2 text-primary">
            <Icon className="h-4 w-4" />
            <span className="text-xs font-semibold uppercase tracking-wide">{title}</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <span className="rounded-sm bg-muted px-1.5 py-0.5 text-xs">{count}</span>
            <ChevronDown className="h-3 w-3" />
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-2 p-3 pt-0">
          {items.map((item) => (
            <div className="rounded-md border border-border/50 bg-muted/20 p-2" key={item.id}>
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="truncate text-xs font-semibold text-foreground">{item.id}</span>
                <span className="truncate text-[10px] uppercase tracking-wide text-muted-foreground">{item.title}</span>
              </div>
              <p className="line-clamp-3 text-xs leading-5 text-muted-foreground">{item.body}</p>
              {item.meta && <p className="mt-1 line-clamp-1 text-[10px] text-muted-foreground/80">{item.meta}</p>}
            </div>
          ))}
          {items.length === 0 && <p className="text-sm text-muted-foreground">{empty}</p>}
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

function InfoPair({label, value}: {label: string; value: string}) {
  return (
    <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="truncate text-right font-medium text-foreground">{value}</span>
    </div>
  );
}

function MiniSection({icon: Icon, title, count, items}: {icon: typeof Scale; title: string; count: number; items: string[]}) {
  return (
    <Collapsible>
      <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md p-2 text-sm font-medium text-muted-foreground hover:bg-accent">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" />
          <span className="text-xs font-semibold uppercase tracking-wide">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-sm bg-muted px-1.5 py-0.5 text-xs">{count}</span>
          <ChevronDown className="h-3 w-3" />
        </div>
      </CollapsibleTrigger>
      <CollapsibleContent className="space-y-2 px-2 pb-3 pt-1">
        {items.slice(0, 4).map((item) => (
          <p className="line-clamp-2 rounded-md bg-background px-2 py-1.5 text-xs leading-5 text-muted-foreground" key={item}>
            {item}
          </p>
        ))}
        {items.length === 0 && <p className="px-2 text-xs text-muted-foreground">Chưa có dữ liệu.</p>}
      </CollapsibleContent>
    </Collapsible>
  );
}

function SidebarNav({icon: Icon, label, active = false}: {icon: typeof Briefcase; label: string; active?: boolean}) {
  return (
    <Button variant="ghost" className={`flex h-auto flex-col gap-1 px-1 py-2 ${active ? 'bg-primary/5 text-primary' : 'text-muted-foreground hover:text-primary'}`}>
      <Icon className="h-4 w-4" />
      <span className="text-[10px]">{label}</span>
    </Button>
  );
}

function TranscriptItem({turn, index}: {turn: CourtroomTurn; index: number}) {
  const tone = speakerColors[turn.speaker] ?? 'slate';
  const toneClass =
    tone === 'blue'
      ? 'border-blue-500/20 bg-blue-500/10 text-blue-600'
      : tone === 'amber'
        ? 'border-amber-500/20 bg-amber-500/10 text-amber-600'
        : tone === 'emerald'
          ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600'
          : tone === 'red'
            ? 'border-red-500/20 bg-red-500/10 text-red-600'
            : tone === 'purple'
              ? 'border-purple-500/20 bg-purple-500/10 text-purple-600'
              : 'border-slate-500/20 bg-slate-500/10 text-slate-600';

  return (
    <div className="group flex gap-5">
      <div className="w-16 shrink-0 pr-2 pt-1 text-right">
        <span className="font-mono text-xs text-muted-foreground">{turnTime(index)}</span>
      </div>
      <div className={`relative mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${toneClass}`}>
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-current/10">
          <span className="text-[12px] font-bold">{initials(turn.speaker_label || turn.speaker)}</span>
        </div>
        <div className="absolute -left-[16px] top-1/2 h-px w-[14px] bg-current/30" />
        <div className="absolute -left-[18px] top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-current" />
      </div>
      <div className="flex-1 pb-4 pt-1">
        <div className="mb-1 flex items-center justify-between gap-3">
          <h4 className="truncate text-[13px] font-bold uppercase tracking-wide text-foreground">
            {turn.speaker_label || turn.speaker}
            <span className="ml-1 font-normal normal-case tracking-normal text-muted-foreground">- {labelStage(turn.trial_stage)}</span>
          </h4>
          <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
            <Badge variant={badgeVariant(turn.status)}>{labelStatus(turn.status)}</Badge>
            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-foreground">
              <MoreVertical className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
        <p className="text-[15px] leading-7 text-foreground/90">{turn.utterance}</p>
        {(turn.evidence_ids.length > 0 || turn.citation_ids.length > 0 || turn.risk_notes.length > 0) && (
          <div className="mt-3 flex flex-wrap gap-2">
            {turn.evidence_ids.map((item) => (
              <Badge variant="outline" key={item}>
                <ShieldCheck className="h-3 w-3" />
                {item}
              </Badge>
            ))}
            {turn.citation_ids.map((item) => (
              <Badge variant="secondary" key={item}>
                <BookOpen className="h-3 w-3" />
                {item}
              </Badge>
            ))}
            {turn.risk_notes.map((item) => (
              <Badge variant="destructive" key={item}>
                <AlertTriangle className="h-3 w-3" />
                {item}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function JudgePanel({title, items, badge, muted = false}: {title: string; items: string[]; badge?: string; muted?: boolean}) {
  return (
    <div className="rounded-lg border border-border bg-background px-3 py-2 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <h4 className="text-[11px] font-semibold uppercase tracking-wider text-foreground/80">{title}</h4>
        {badge && <span className="rounded border border-border bg-muted px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-muted-foreground">{badge}</span>}
      </div>
      <ul className="space-y-1.5 text-xs leading-5 text-muted-foreground">
        {items.length > 0 ? (
          items.map((item) => (
            <li className="flex items-start gap-2" key={item}>
              <CheckCircle2 className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${muted ? 'text-muted-foreground/50' : 'text-primary'}`} />
              <span className="line-clamp-2">{item}</span>
            </li>
          ))
        ) : (
          <li className="text-muted-foreground">Chưa có dữ liệu từ stage này.</li>
        )}
      </ul>
    </div>
  );
}

function RightToggle({icon: Icon, title, count}: {icon: typeof ShieldAlert; title: string; count: number}) {
  return (
    <Collapsible>
      <CollapsibleTrigger className="group flex w-full items-center justify-between rounded-lg border border-border/50 bg-background p-3 transition-colors hover:bg-accent/50">
        <div className="flex items-center gap-2 text-muted-foreground transition-colors group-hover:text-primary">
          <Icon className="h-4 w-4" />
          <span className="text-xs font-semibold uppercase tracking-wide">{title}</span>
        </div>
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="rounded-sm bg-muted px-1.5 py-0.5 text-xs">{count}</span>
          <ChevronDown className="h-3 w-3" />
        </div>
      </CollapsibleTrigger>
    </Collapsible>
  );
}

function StatusLine({label, count, tone, strong = false}: {label: string; count: number; tone: 'green' | 'yellow' | 'zinc'; strong?: boolean}) {
  const toneClass =
    tone === 'green'
      ? 'border-green-500/50 bg-green-500/20 text-green-600'
      : tone === 'yellow'
        ? 'border-yellow-500/50 bg-yellow-500/20 text-yellow-600'
        : 'border-zinc-500/50 bg-zinc-500/20 text-zinc-600';
  return (
    <div className="group flex cursor-pointer items-center justify-between">
      <div className="flex items-center gap-2">
        <div className={`flex h-3 w-3 items-center justify-center rounded-full border ${toneClass}`}>
          {tone === 'green' ? <CheckCircle2 className="h-2 w-2" /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
        </div>
        <span className={strong ? 'font-medium text-foreground group-hover:underline' : 'text-muted-foreground transition-colors group-hover:text-foreground'}>{label}</span>
      </div>
      <span className={strong ? 'rounded border border-primary/20 bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary' : 'rounded bg-muted px-2 py-0.5 text-xs'}>{count}</span>
    </div>
  );
}

function ProgressPill({label, index, done = false, active = false}: {label: string; index: number; done?: boolean; active?: boolean}) {
  return (
    <div className={`flex items-center gap-2 ${done ? 'text-green-600' : active ? 'text-primary' : ''}`}>
      <div className={`${done ? 'bg-green-600 text-white' : active ? 'bg-primary text-white' : 'bg-muted text-muted-foreground'} flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold`}>
        {done ? <CheckCircle2 className="h-3 w-3" /> : index}
      </div>
      <span className="hidden lg:inline">{label}</span>
    </div>
  );
}

function ProgressBar() {
  return <div className="mx-1 h-px w-6 bg-border" />;
}
