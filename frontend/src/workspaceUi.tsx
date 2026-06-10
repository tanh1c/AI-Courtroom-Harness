import {
  AlertTriangle,
  BookOpen,
  Briefcase,
  CheckCircle2,
  ChevronDown,
  MoreVertical,
  Scale,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react';

import {CaseDetail, CaseRecord, CourtroomTurn} from './api';
import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Card} from '@/components/ui/card';
import {Collapsible, CollapsibleContent, CollapsibleTrigger} from '@/components/ui/collapsible';

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

export function labelStage(stage?: string) {
  if (!stage) return 'Chưa khởi động';
  return stageLabels[stage] ?? stage.replaceAll('_', ' ');
}

export function labelStatus(status?: string) {
  if (!status) return 'Chưa có dữ liệu';
  return statusLabels[status] ?? status.replaceAll('_', ' ');
}

export function badgeVariant(status?: string): 'default' | 'secondary' | 'destructive' | 'outline' {
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

export function getCaseTitle(caseDetail: CaseDetail | null, selectedCase: CaseRecord | undefined) {
  return caseDetail?.record.title || selectedCase?.title || 'Chưa chọn hồ sơ';
}

export function escapeHtml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}


export function CompactJudgeCard({title, value, muted = false, accent = false}: {title: string; value: string; muted?: boolean; accent?: boolean}) {
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

export function InfoLine({label, value}: {label: string; value: string}) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border/50 pb-1 last:border-b-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="max-w-[170px] truncate text-right text-xs font-medium text-foreground">{value}</span>
    </div>
  );
}

export function DataPanel({
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

export function InfoPair({label, value}: {label: string; value: string}) {
  return (
    <div className="grid grid-cols-[80px_1fr] gap-2 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="truncate text-right font-medium text-foreground">{value}</span>
    </div>
  );
}

export function MiniSection({icon: Icon, title, count, items}: {icon: typeof Scale; title: string; count: number; items: string[]}) {
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

export function SidebarNav({icon: Icon, label, active = false}: {icon: typeof Briefcase; label: string; active?: boolean}) {
  return (
    <Button variant="ghost" className={`flex h-auto flex-col gap-1 px-1 py-2 ${active ? 'bg-primary/5 text-primary' : 'text-muted-foreground hover:text-primary'}`}>
      <Icon className="h-4 w-4" />
      <span className="text-[10px]">{label}</span>
    </Button>
  );
}

export function TranscriptItem({turn, index}: {turn: CourtroomTurn; index: number}) {
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

export function JudgePanel({title, items, badge, muted = false}: {title: string; items: string[]; badge?: string; muted?: boolean}) {
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

export function RightToggle({icon: Icon, title, count}: {icon: typeof ShieldAlert; title: string; count: number}) {
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

export function StatusLine({label, count, tone, strong = false}: {label: string; count: number; tone: 'green' | 'yellow' | 'zinc'; strong?: boolean}) {
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

export function ProgressPill({label, index, done = false, active = false}: {label: string; index: number; done?: boolean; active?: boolean}) {
  return (
    <div className={`flex items-center gap-2 ${done ? 'text-green-600' : active ? 'text-primary' : ''}`}>
      <div className={`${done ? 'bg-green-600 text-white' : active ? 'bg-primary text-white' : 'bg-muted text-muted-foreground'} flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold`}>
        {done ? <CheckCircle2 className="h-3 w-3" /> : index}
      </div>
      <span className="hidden lg:inline">{label}</span>
    </div>
  );
}

export function ProgressBar() {
  return <div className="mx-1 h-px w-6 bg-border" />;
}
