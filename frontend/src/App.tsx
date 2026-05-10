import {useEffect, useMemo, useState} from 'react';
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  FileText,
  Gavel,
  Loader2,
  Play,
  RefreshCw,
  Scale3d,
  ShieldCheck,
  Upload,
} from 'lucide-react';

import {
  CaseRecord,
  CourtroomTurn,
  V2UiState,
  exportV2Html,
  getV2UiState,
  healthCheck,
  listCases,
  runExistingV2Pipeline,
  runV2Pipeline,
} from './api';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {ScrollArea} from '@/components/ui/scroll-area';
import {Separator} from '@/components/ui/separator';

const DEFAULT_NARRATIVE =
  'Nguyên đơn cho rằng bị đơn vi phạm nghĩa vụ trong hợp đồng mua bán tài sản. Các bên tranh chấp về thời hạn giao tài sản, điều kiện thanh toán còn lại, nghĩa vụ hoàn trả tiền đã nhận và bồi thường chi phí phát sinh.';

const stageLabels: Record<string, string> = {
  case_preparation: 'Chuẩn bị hồ sơ',
  opening_formalities: 'Mở phiên',
  appearance_check: 'Kiểm tra sự có mặt',
  procedure_explanation: 'Phổ biến thủ tục',
  plaintiff_claim_statement: 'Nguyên đơn trình bày',
  defense_response_statement: 'Bị đơn đối đáp',
  evidence_examination: 'Xem xét chứng cứ',
  judge_examination: 'HĐXX hỏi',
  plaintiff_debate: 'Tranh luận của nguyên đơn',
  defense_rebuttal: 'Đối đáp của bị đơn',
  final_statements: 'Lời nói sau cùng',
  deliberation: 'Nghị án mô phỏng',
  simulated_decision: 'Kết quả mô phỏng',
  closing_record: 'Kết thúc phiên',
};

const speakerLabels: Record<string, string> = {
  plaintiff_agent: 'Nguyên đơn',
  defense_agent: 'Bị đơn',
  judge_agent: 'Hội đồng xét xử',
  clerk_agent: 'Thư ký',
  prosecutor_agent: 'Kiểm sát viên',
  evidence_agent: 'Tác nhân chứng cứ',
  legal_retrieval_agent: 'Tác nhân pháp luật',
  fact_check_agent: 'Tác nhân xác minh',
  citation_verifier_agent: 'Tác nhân kiểm tra viện dẫn',
};

function labelStage(stage: string) {
  return stageLabels[stage] ?? stage.replaceAll('_', ' ');
}

function speakerName(turn: CourtroomTurn) {
  return turn.speaker_label || speakerLabels[turn.speaker] || turn.speaker;
}

function statusVariant(status: string) {
  if (status === 'report_ready' || status === 'ok') return 'secondary';
  if (status.includes('review') || status.includes('blocked')) return 'destructive';
  return 'outline';
}

export default function App() {
  const [apiOnline, setApiOnline] = useState(false);
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [uiState, setUiState] = useState<V2UiState | null>(null);
  const [title, setTitle] = useState('V2 Civil Contract Simulation');
  const [narrative, setNarrative] = useState(DEFAULT_NARRATIVE);
  const [files, setFiles] = useState<File[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [htmlPreview, setHtmlPreview] = useState('');
  const [markdownPath, setMarkdownPath] = useState('');
  const [htmlPath, setHtmlPath] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const selectedCase = useMemo(
    () => cases.find((item) => item.case_id === selectedCaseId),
    [cases, selectedCaseId],
  );

  async function refreshCases(preferredCaseId?: string) {
    setError('');
    const [online, records] = await Promise.all([healthCheck(), listCases()]);
    setApiOnline(online);
    setCases(records);
    const nextCaseId = preferredCaseId || selectedCaseId || records[0]?.case_id || '';
    setSelectedCaseId(nextCaseId);
    if (nextCaseId) {
      await refreshUiState(nextCaseId, false);
    }
  }

  async function refreshUiState(caseId = selectedCaseId, showError = true) {
    if (!caseId) return;
    try {
      const state = await getV2UiState(caseId);
      setUiState(state);
    } catch (exc) {
      setUiState(null);
      if (showError) {
        setError(exc instanceof Error ? exc.message : String(exc));
      }
    }
  }

  useEffect(() => {
    refreshCases().catch((exc) => {
      setError(exc instanceof Error ? exc.message : String(exc));
    });
    // Initial load only; later refreshes are user-driven.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runPipelineForCase(caseId: string) {
    setBusy(true);
    setError('');
    setLogs([]);
    setHtmlPreview('');
    try {
      const result = await runExistingV2Pipeline(caseId, (message) => {
        setLogs((current) => [...current, message]);
      });
      setUiState(result.uiState);
      setMarkdownPath(result.markdownPath || '');
      setHtmlPath(result.htmlPath || '');
      setHtmlPreview(result.html || '');
      await refreshCases(caseId);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(false);
    }
  }

  async function createAndRunPipeline() {
    setBusy(true);
    setError('');
    setLogs([]);
    setHtmlPreview('');
    try {
      const result = await runV2Pipeline({
        title,
        narrative,
        files,
        onStep: (message) => setLogs((current) => [...current, message]),
      });
      setUiState(result.uiState);
      setMarkdownPath(result.markdownPath || '');
      setHtmlPath(result.htmlPath || '');
      setHtmlPreview(result.html || '');
      await refreshCases(result.caseId);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(false);
    }
  }

  async function previewCurrentHtml() {
    if (!selectedCaseId) return;
    setBusy(true);
    setError('');
    try {
      const result = await exportV2Html(selectedCaseId);
      setHtmlPath(result.htmlPath);
      setHtmlPreview(result.html);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-xl border bg-muted">
              <Scale3d className="size-6 text-primary" />
            </div>
            <div>
              <p className="font-heading text-xl font-semibold tracking-tight">AI Courtroom Harness</p>
              <p className="text-sm text-muted-foreground">V2 simulated trial pipeline control room</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={apiOnline ? 'secondary' : 'destructive'}>
              {apiOnline ? 'API online' : 'API offline'}
            </Badge>
            <Badge variant="outline">{selectedCaseId || 'No case selected'}</Badge>
            <Button variant="outline" onClick={() => refreshCases()} disabled={busy}>
              <RefreshCw className="size-4" />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-4 px-5 py-5 lg:grid-cols-[300px_1fr_360px]">
        <aside className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Case Intake</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="block text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Existing case
              </label>
              <select
                className="h-10 w-full rounded-lg border bg-background px-3 text-sm"
                value={selectedCaseId}
                onChange={(event) => {
                  setSelectedCaseId(event.target.value);
                  refreshUiState(event.target.value).catch(() => undefined);
                }}
              >
                <option value="">Select a case</option>
                {cases.map((item) => (
                  <option key={item.case_id} value={item.case_id}>
                    {item.case_id} - {item.title}
                  </option>
                ))}
              </select>
              <Button
                className="w-full"
                disabled={!selectedCaseId || busy}
                onClick={() => runPipelineForCase(selectedCaseId)}
              >
                {busy ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
                Run selected through V2
              </Button>
              <Separator />
              <label className="block text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                New case title
              </label>
              <input
                className="h-10 w-full rounded-lg border bg-background px-3 text-sm"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
              <label className="block text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Narrative
              </label>
              <textarea
                className="min-h-32 w-full rounded-lg border bg-background px-3 py-2 text-sm leading-6"
                value={narrative}
                onChange={(event) => setNarrative(event.target.value)}
              />
              <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed px-3 py-4 text-sm text-muted-foreground">
                <Upload className="size-4" />
                Attach PDFs or evidence files
                <input
                  className="hidden"
                  multiple
                  type="file"
                  onChange={(event) => setFiles(Array.from(event.target.files || []))}
                />
              </label>
              {files.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {files.length} file(s): {files.map((file) => file.name).join(', ')}
                </p>
              )}
              <Button className="w-full" disabled={busy || !title || !narrative} onClick={createAndRunPipeline}>
                {busy ? <Loader2 className="size-4 animate-spin" /> : <Gavel className="size-4" />}
                Create and run full V2
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Run Log</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                {logs.length === 0 && <p className="text-muted-foreground">No pipeline steps yet.</p>}
                {logs.map((item, index) => (
                  <div key={`${item}-${index}`} className="flex gap-2">
                    <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-primary" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </aside>

        <section className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <CardTitle>{selectedCase?.title || 'No V2 trial loaded'}</CardTitle>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Current stage: {uiState ? labelStage(uiState.current_stage) : 'Not started'}
                  </p>
                </div>
                <Badge variant={statusVariant(uiState?.status || selectedCase?.status || 'draft')}>
                  {uiState?.status || selectedCase?.status || 'draft'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {(uiState?.timeline || []).map((item) => (
                  <div
                    className="rounded-lg border bg-background p-3"
                    key={item.trial_stage}
                  >
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {item.status}
                    </p>
                    <p className="mt-1 text-sm font-medium">{labelStage(item.trial_stage)}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{item.turn_ids.length} turn(s)</p>
                  </div>
                ))}
                {!uiState && <p className="text-sm text-muted-foreground">Start or refresh a V2 trial to see stages.</p>}
              </div>
            </CardContent>
          </Card>

          <Card className="min-h-[560px]">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Biên bản phiên tòa</CardTitle>
                <Badge variant="outline">{uiState?.transcript.length || 0} lượt thoại</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px] pr-4">
                <div className="relative space-y-5 border-l pl-5">
                  {(uiState?.transcript || []).map((turn) => (
                    <div key={turn.turn_id}>
                      <TranscriptTurn turn={turn} />
                    </div>
                  ))}
                  {!uiState?.transcript.length && (
                    <p className="text-sm text-muted-foreground">
                      Transcript will appear here after the V2 runtime advances.
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </section>

        <aside className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Verification</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <InfoRow label="Human review" value={uiState?.human_review.blocked ? 'Blocked' : 'Optional/clear'} />
              <InfoRow
                label="Decision guard"
                value={uiState?.decision_guard?.allowed_to_emit ? 'Allowed' : 'Needs review or pending'}
              />
              <InfoRow
                label="Dialogue issues"
                value={`${uiState?.dialogue_quality.ungrounded_turn_ids.length || 0} ungrounded`}
              />
              {uiState?.human_review.checklist?.length ? (
                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Review checklist
                  </p>
                  <ul className="space-y-2">
                    {uiState.human_review.checklist.map((item) => (
                      <li className="flex gap-2" key={item}>
                        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Evidence & Citations</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {(uiState?.evidence_examinations || []).slice(0, 5).map((item) => (
                <div className="rounded-lg border p-3" key={item.examination_id}>
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium">{item.evidence_id}</p>
                    <Badge variant="outline">{item.admissibility}</Badge>
                  </div>
                  <p className="mt-2 text-muted-foreground">{item.notes || item.plaintiff_position}</p>
                </div>
              ))}
              {uiState?.simulated_decision?.citation_ids?.length ? (
                <div>
                  <p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    <BookOpen className="size-4" />
                    Citations used
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {uiState.simulated_decision.citation_ids.map((item) => (
                      <Badge key={item} variant="secondary">
                        {item}
                      </Badge>
                    ))}
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Outcome & Export</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {uiState?.simulated_decision ? (
                <div className="rounded-lg border bg-muted/40 p-3">
                  <p className="font-medium">{uiState.simulated_decision.disposition}</p>
                  <p className="mt-2 leading-6 text-muted-foreground">{uiState.simulated_decision.summary}</p>
                </div>
              ) : (
                <p className="text-muted-foreground">Decision appears after the simulated decision stage.</p>
              )}
              <Button className="w-full" variant="outline" disabled={!selectedCaseId || busy} onClick={previewCurrentHtml}>
                <FileText className="size-4" />
                Export / refresh HTML preview
              </Button>
              {markdownPath && <InfoRow label="Markdown" value={markdownPath} />}
              {htmlPath && <InfoRow label="HTML" value={htmlPath} />}
            </CardContent>
          </Card>
        </aside>
      </main>

      {htmlPreview && (
        <section className="mx-auto max-w-7xl px-5 pb-8">
          <Card>
            <CardHeader>
              <CardTitle>HTML Report Preview</CardTitle>
            </CardHeader>
            <CardContent>
              <iframe
                className="h-[680px] w-full rounded-lg border bg-white"
                srcDoc={htmlPreview}
                title="V2 report preview"
              />
            </CardContent>
          </Card>
        </section>
      )}

      {error && (
        <div className="fixed bottom-4 right-4 max-w-xl rounded-lg border border-destructive/30 bg-background p-4 text-sm shadow-lg">
          <div className="flex gap-2">
            <AlertTriangle className="size-4 shrink-0 text-destructive" />
            <p>{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function TranscriptTurn({turn}: {turn: CourtroomTurn}) {
  return (
    <article className="relative rounded-xl border bg-card p-4 shadow-sm">
      <div className="absolute -left-[29px] top-5 size-3 rounded-full border bg-background" />
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {labelStage(turn.trial_stage)}
          </p>
          <h3 className="mt-1 font-heading text-lg font-semibold">{speakerName(turn)}</h3>
        </div>
        <Badge variant={statusVariant(turn.status)}>{turn.status}</Badge>
      </div>
      <p className="mt-3 whitespace-pre-wrap text-[15px] leading-7">{turn.utterance}</p>
      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        {turn.evidence_ids.map((item) => (
          <Badge key={item} variant="outline">
            <ShieldCheck className="size-3" />
            {item}
          </Badge>
        ))}
        {turn.citation_ids.map((item) => (
          <Badge key={item} variant="secondary">
            <BookOpen className="size-3" />
            {item}
          </Badge>
        ))}
      </div>
    </article>
  );
}

function InfoRow({label, value}: {label: string; value: string}) {
  return (
    <div className="flex items-start justify-between gap-3 border-b pb-2 last:border-b-0 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="max-w-[210px] break-words text-right font-medium">{value}</span>
    </div>
  );
}
