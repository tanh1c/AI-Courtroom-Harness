import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  FileText,
  GitBranch,
  Layers3,
  Scale,
  Scale3d,
  Server,
  ShieldCheck,
  Workflow,
} from 'lucide-react';

import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {Card} from '@/components/ui/card';
import {ScrollArea} from '@/components/ui/scroll-area';
import {Separator} from '@/components/ui/separator';

type ProductOverviewPageProps = {
  onBack: () => void;
};

const versions = [
  {
    name: 'MVP',
    status: 'Milestone F closed',
    focus: 'Case intake, baseline simulation, human review, and report preview.',
    features: [
      'Create civil-contract cases and upload attachments',
      'Parse facts, evidence, claims, legal issues, and citations',
      'Run structured simulation with audit and review gate',
      'Approve human review and export persisted markdown report',
    ],
    tech: [
      'FastAPI case store and SQLite-backed processed data',
      'Pydantic contracts mirrored by frontend TypeScript',
      'Heuristic parser and retrieval-backed simulation service',
      'Markdown report renderer for review-ready output',
    ],
  },
  {
    name: 'V1',
    status: 'Procedural hearing harness',
    focus: 'A fuller simulated hearing with challenge, verification, and outcome surfaces.',
    features: [
      'Stage-based hearing: opening through closing record',
      'Evidence challenge flow with admissibility state',
      'Fact-check and citation-verifier turns',
      'Clarification questions, party responses, and non-binding proposed outcome',
    ],
    tech: [
      'HearingSession runtime with enforced stage order',
      'Dedicated V1 endpoints for hearing, challenges, verification, and outcome',
      'Formal V1 markdown and HTML hearing record exports',
      'Human review remains mandatory before outcome use',
    ],
  },
  {
    name: 'V2',
    status: 'Courtroom-style trial record',
    focus: 'Vietnamese courtroom narrative from preparation to simulated decision.',
    features: [
      'Complete trial timeline with clerk, judge, parties, and evidence agent',
      'Evidence examination, debate, final statements, and deliberation',
      'Simulation-safe decision guard and optional review checklist',
      'Formal HTML/Markdown trial record preview',
    ],
    tech: [
      'V2TrialSession contracts and timeline UI-state endpoint',
      'CourtroomDialogueTurn and EvidenceExamination surfaces',
      'DecisionGuardResult blocks official judgment language',
      'Frontend renders transcript, citations, debate, risks, and exports',
    ],
  },
];

const architecture = [
  ['Data Plane', 'Case input, uploaded attachments, parsed facts, evidence, issues, claims, and citations.'],
  ['Runtime Plane', 'MVP simulation, V1 hearing runtime, and V2 trial runtime share backend contracts but expose different depth.'],
  ['Verification Plane', 'Fact-checking, citation verification, audit events, role/stage safety, and review checklists.'],
  ['Reporting Plane', 'Markdown and HTML renderers produce records that remain readable outside the frontend.'],
  ['UI Plane', 'React/Vite workspace with MVP, V1, and V2 modes over the same case store.'],
];

const flow = [
  'Create or choose a case',
  'Upload attachments',
  'Parse case state',
  'Run MVP/V1/V2 flow',
  'Inspect evidence and citations',
  'Review risks and outcome',
  'Export report',
];

export function ProductOverviewPage({onBack}: ProductOverviewPageProps) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur">
        <div className="flex min-w-0 items-center gap-4">
          <Button variant="ghost" size="icon" className="h-9 w-9" onClick={onBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-3 font-serif font-bold uppercase leading-[1.1] tracking-widest text-primary">
            <Scale3d className="h-9 w-9" />
            <div className="flex flex-col pt-1">
              <span className="text-xl">AI Courtroom</span>
              <span className="font-sans text-[12px] tracking-[0.4em] text-primary/70">Product</span>
            </div>
          </div>
          <Separator orientation="vertical" className="mx-2 h-8" />
          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold">AI Courtroom Harness overview</h1>
            <p className="truncate text-xs text-muted-foreground">Feature map, product boundary, and technical architecture for MVP, V1, and V2.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">MVP closed</Badge>
          <Badge variant="outline">V1/V2 ready</Badge>
        </div>
      </header>

      <ScrollArea className="min-h-0 flex-1">
        <main className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-5">
          <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded bg-primary/10 text-primary">
                  <Scale className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="font-serif text-xl font-bold uppercase tracking-wide">Legal simulation, not automated judging</h2>
                  <p className="mt-1 text-sm leading-6 text-muted-foreground">
                    The product helps inspect a Vietnamese civil-contract dispute through structured evidence, agent dialogue, verification, human review, and exportable simulated records.
                  </p>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <Signal label="Primary case type" value="civil_contract_dispute" />
                <Signal label="Frontend modes" value="MVP / V1 / V2" />
                <Signal label="Safety boundary" value="Non-binding simulation" />
              </div>
            </div>

            <Card className="border-border/50 bg-card p-5 shadow-sm">
              <div className="mb-3 flex items-center gap-2 text-primary">
                <Workflow className="h-4 w-4" />
                <h3 className="text-xs font-semibold uppercase tracking-wide">End-to-end flow</h3>
              </div>
              <div className="space-y-2">
                {flow.map((step, index) => (
                  <div className="flex items-center gap-3" key={step}>
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-primary/30 bg-primary/10 text-xs font-bold text-primary">
                      {index + 1}
                    </div>
                    <p className="text-sm text-foreground/90">{step}</p>
                  </div>
                ))}
              </div>
            </Card>
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            {versions.map((version) => (
              <Card className="border-border/50 bg-card p-4 shadow-sm" key={version.name}>
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <p className="font-serif text-lg font-bold uppercase tracking-wide text-primary">{version.name}</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{version.focus}</p>
                  </div>
                  <Badge variant="secondary" className="shrink-0">{version.status}</Badge>
                </div>
                <BlockTitle icon={CheckCircle2} title="Product features" />
                <ul className="mb-4 space-y-2">
                  {version.features.map((item) => (
                    <li className="flex gap-2 text-sm leading-6 text-muted-foreground" key={item}>
                      <CheckCircle2 className="mt-1 h-3.5 w-3.5 shrink-0 text-primary" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
                <BlockTitle icon={Server} title="Technical notes" />
                <ul className="space-y-2">
                  {version.tech.map((item) => (
                    <li className="flex gap-2 text-xs leading-5 text-muted-foreground" key={item}>
                      <GitBranch className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            ))}
          </section>

          <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
            <Card className="border-border/50 bg-card p-4 shadow-sm">
              <BlockTitle icon={Layers3} title="Architecture layers" />
              <div className="space-y-3">
                {architecture.map(([name, detail]) => (
                  <div className="rounded-md border border-border/50 bg-background p-3" key={name}>
                    <p className="text-xs font-semibold uppercase tracking-wide text-foreground">{name}</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{detail}</p>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="border-border/50 bg-card p-4 shadow-sm">
              <BlockTitle icon={ShieldCheck} title="Safety and review model" />
              <div className="grid gap-3 sm:grid-cols-2">
                <SafetyItem title="Grounding first" detail="Important claims carry evidence IDs and citation IDs where available; weak support becomes a review item." />
                <SafetyItem title="No official judgment" detail="Prompts, guards, and product copy avoid official court-order language." />
                <SafetyItem title="Human review" detail="MVP and V1 expose review gates; V2 surfaces optional review checklist and risk notes." />
                <SafetyItem title="Portable record" detail="Markdown/HTML exports remain readable without the React frontend." />
              </div>
              <Separator className="my-4" />
              <div className="rounded-md border border-primary/20 bg-primary/5 p-3">
                <div className="mb-2 flex items-center gap-2 text-primary">
                  <BookOpen className="h-4 w-4" />
                  <p className="text-xs font-semibold uppercase tracking-wide">Current frontend status</p>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">
                  The workspace now closes the original MVP frontend checklist and adds V1/V2 inspection modes: evidence tables, citations, transcript, review flags, verification, challenges, outcomes, and report previews.
                </p>
              </div>
            </Card>
          </section>

          <section className="rounded-lg border border-border bg-card p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2 text-primary">
              <FileText className="h-4 w-4" />
              <h3 className="text-xs font-semibold uppercase tracking-wide">What each page is for</h3>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <Usage title="MVP mode" detail="Use for a fast product demo: create/upload/parse/simulate/approve/export." />
              <Usage title="V1 mode" detail="Use for procedural harness inspection: hearing stages, evidence challenges, verification turns, and proposed outcome." />
              <Usage title="V2 mode" detail="Use for polished courtroom storytelling: formal transcript, evidence examination, deliberation, and simulated decision." />
            </div>
          </section>
        </main>
      </ScrollArea>
    </div>
  );
}

function BlockTitle({icon: Icon, title}: {icon: typeof Scale; title: string}) {
  return (
    <div className="mb-2 flex items-center gap-2 text-primary">
      <Icon className="h-4 w-4" />
      <h3 className="text-xs font-semibold uppercase tracking-wide">{title}</h3>
    </div>
  );
}

function Signal({label, value}: {label: string; value: string}) {
  return (
    <div className="rounded-md border border-border/50 bg-background p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function SafetyItem({title, detail}: {title: string; detail: string}) {
  return (
    <div className="rounded-md border border-border/50 bg-background p-3">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">{detail}</p>
    </div>
  );
}

function Usage({title, detail}: {title: string; detail: string}) {
  return (
    <div className="rounded-md border border-border/50 bg-background p-3">
      <p className="text-sm font-semibold text-foreground">{title}</p>
      <p className="mt-1 text-sm leading-6 text-muted-foreground">{detail}</p>
    </div>
  );
}
