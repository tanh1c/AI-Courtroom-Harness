import {useState} from 'react';
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Database,
  FileText,
  GitBranch,
  Layers3,
  Scale,
  Scale3d,
  ShieldAlert,
  ShieldCheck,
  Workflow,
} from 'lucide-react';

import {Badge} from '@/components/ui/badge';
import {Button} from '@/components/ui/button';
import {ScrollArea} from '@/components/ui/scroll-area';
import {Separator} from '@/components/ui/separator';

type ProductOverviewPageProps = {
  onBack: () => void;
};

type VersionName = 'MVP' | 'V1' | 'V2';

const versions: Record<
  VersionName,
  {
    status: string;
    role: string;
    promise: string;
    features: string[];
    tech: string[];
    surfaces: string[];
  }
> = {
  MVP: {
    status: 'Milestone F closed',
    role: 'Product demo path',
    promise: 'Turns a civil-contract case into a reviewed, exportable decision-support report.',
    features: [
      'Create case and upload evidence attachments',
      'Parse facts, evidence, legal issues, claims, and citations',
      'Run structured simulation with audit trail',
      'Approve human review and export persisted markdown',
    ],
    tech: [
      'FastAPI case store and SQLite-backed processed data',
      'Pydantic schemas mirrored by TypeScript contracts',
      'Heuristic parser plus retrieval-backed simulation',
      'Markdown renderer for review-ready reports',
    ],
    surfaces: ['Case intake', 'Evidence table', 'Audit trail', 'Review gate', 'Report preview'],
  },
  V1: {
    status: 'Procedural harness ready',
    role: 'Hearing inspection path',
    promise: 'Expands the simulation into a stage-based hearing with challenges, verification, and outcome candidates.',
    features: [
      'Stage-based hearing from opening to closing record',
      'Evidence challenge flow and admissibility state',
      'Fact-check and citation-verifier turns',
      'Clarification questions, party responses, and proposed outcome',
    ],
    tech: [
      'HearingSession runtime with guarded stage order',
      'Dedicated endpoints for hearing/challenges/verification/outcome',
      'Formal V1 markdown and HTML hearing records',
      'Mandatory human review before outcome use',
    ],
    surfaces: ['Stage timeline', 'Challenges', 'Verification turns', 'Clarification', 'Outcome candidates'],
  },
  V2: {
    status: 'Courtroom record ready',
    role: 'Formal trial narrative path',
    promise: 'Creates a Vietnamese courtroom-style record with evidence examination, deliberation, and guarded simulated decision.',
    features: [
      'Complete trial timeline with clerk, judge, parties, and evidence agent',
      'Evidence examination, debate, final statements, and deliberation',
      'Simulation-safe decision guard and review checklist',
      'Formal HTML/Markdown trial record preview',
    ],
    tech: [
      'V2TrialSession and timeline UI-state endpoint',
      'CourtroomDialogueTurn and EvidenceExamination surfaces',
      'DecisionGuardResult blocks official judgment language',
      'Frontend renders transcript, risks, debate, citations, and exports',
    ],
    surfaces: ['Trial timeline', 'Transcript', 'Evidence examination', 'Deliberation', 'Simulated decision'],
  },
};

const architecture = [
  {
    name: 'Data Plane',
    icon: Database,
    detail: 'Case input, attachment metadata, parsed facts, evidence, issues, claims, and citations.',
    tone: 'border-blue-500/20 bg-blue-500/5 text-blue-600',
  },
  {
    name: 'Runtime Plane',
    icon: Workflow,
    detail: 'MVP simulation, V1 hearing runtime, and V2 trial runtime share contracts but expose different procedural depth.',
    tone: 'border-emerald-500/20 bg-emerald-500/5 text-emerald-600',
  },
  {
    name: 'Verification Plane',
    icon: ShieldCheck,
    detail: 'Fact checking, citation verification, audit events, role/stage safety, and review checklist propagation.',
    tone: 'border-amber-500/20 bg-amber-500/5 text-amber-600',
  },
  {
    name: 'Reporting Plane',
    icon: FileText,
    detail: 'Markdown and HTML renderers produce records that remain readable without the React app.',
    tone: 'border-red-500/20 bg-red-500/5 text-red-600',
  },
  {
    name: 'UI Plane',
    icon: Layers3,
    detail: 'React/Vite workspace with MVP, V1, and V2 modes over the same backend case store.',
    tone: 'border-primary/20 bg-primary/5 text-primary',
  },
];

const flow = ['Create', 'Upload', 'Parse', 'Run mode', 'Inspect', 'Review', 'Export'];

const guardrails = [
  ['Grounding first', 'Important claims carry evidence IDs and citation IDs when available. Missing support becomes review work.'],
  ['No official judgment', 'The product avoids official court-order language and labels outcomes as non-binding simulations.'],
  ['Human review', 'MVP and V1 expose review gates. V2 surfaces optional review checklist and risk notes.'],
  ['Portable records', 'Markdown and HTML exports can be read without the frontend, which keeps demos reproducible.'],
];

const pageSections = [
  {id: 'overview', label: 'Overview', icon: Scale},
  {id: 'versions', label: 'Version modes', icon: GitBranch},
  {id: 'flow', label: 'Operating flow', icon: Workflow},
  {id: 'architecture', label: 'Architecture', icon: Layers3},
  {id: 'safety', label: 'Safety stack', icon: ShieldCheck},
];

export function ProductOverviewPage({onBack}: ProductOverviewPageProps) {
  const [selectedVersion, setSelectedVersion] = useState<VersionName>('V2');
  const version = versions[selectedVersion];

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
            <h1 className="truncate text-sm font-semibold">Product operating map</h1>
            <p className="truncate text-xs text-muted-foreground">A courtroom-style explanation of features, versions, architecture, and safety boundaries.</p>
          </div>
        </div>
        <Badge variant="secondary" className="hidden sm:inline-flex">MVP / V1 / V2</Badge>
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="hidden w-[292px] shrink-0 border-r border-border bg-card/70 lg:flex lg:flex-col">
          <div className="border-b border-border p-4">
            <div className="mb-3 flex items-center gap-2 text-primary">
              <Scale3d className="h-5 w-5" />
              <p className="text-xs font-semibold uppercase tracking-[0.22em]">Product nav</p>
            </div>
            <p className="text-sm leading-6 text-muted-foreground">
              Explore the product story by section, then switch between MVP, V1, and V2 without leaving the overview.
            </p>
          </div>

          <div className="min-h-0 flex-1 space-y-5 overflow-y-auto p-4 [scrollbar-width:thin] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-border">
            <nav className="space-y-1" aria-label="Product overview sections">
              {pageSections.map((section) => {
                const Icon = section.icon;
                return (
                  <a
                    className="group flex items-center gap-3 rounded-md border border-transparent px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:border-border hover:bg-background hover:text-foreground"
                    href={`#${section.id}`}
                    key={section.id}
                  >
                    <Icon className="h-4 w-4 text-primary/70 group-hover:text-primary" />
                    <span>{section.label}</span>
                  </a>
                );
              })}
            </nav>

            <Separator />

            <div>
              <div className="mb-3 flex items-center gap-2 text-primary">
                <GitBranch className="h-4 w-4" />
                <h3 className="text-xs font-semibold uppercase tracking-wide">Version modes</h3>
              </div>
              <div className="relative space-y-3">
                <div className="absolute bottom-8 left-[21px] top-8 w-px bg-border" />
                {(Object.keys(versions) as VersionName[]).map((name) => (
                  <button
                    className={`relative z-10 flex w-full items-center gap-3 rounded-md border p-3 text-left transition-colors ${
                      selectedVersion === name ? 'border-primary/30 bg-primary/5 text-primary' : 'border-border bg-background text-foreground hover:bg-muted/50'
                    }`}
                    key={name}
                    onClick={() => setSelectedVersion(name)}
                    type="button"
                  >
                    <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full border font-serif text-sm font-bold ${selectedVersion === name ? 'border-primary bg-background' : 'border-border bg-muted'}`}>
                      {name}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold">{versions[name].role}</p>
                      <p className="mt-0.5 truncate text-xs text-muted-foreground">{versions[name].status}</p>
                    </div>
                    <ArrowRight className={`ml-auto h-4 w-4 ${selectedVersion === name ? 'opacity-100' : 'opacity-30'}`} />
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="border-t border-border p-4">
            <div className="rounded-md border border-amber-500/20 bg-amber-500/5 p-3">
              <div className="mb-1 flex items-center gap-2 text-amber-600">
                <ShieldAlert className="h-4 w-4" />
                <p className="text-xs font-semibold uppercase tracking-wide">Boundary</p>
              </div>
              <p className="text-xs leading-5 text-muted-foreground">Simulation and review support only. No official judgment is issued.</p>
            </div>
          </div>
        </aside>

        <ScrollArea className="min-h-0 flex-1">
          <main className="mx-auto flex max-w-7xl flex-col gap-6 px-5 py-5">
          <section className="grid gap-3 lg:hidden">
            <div className="overflow-x-auto rounded-lg border border-border bg-card p-2 [scrollbar-width:thin] [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-border">
              <div className="flex min-w-max gap-2">
                {pageSections.map((section) => {
                  const Icon = section.icon;
                  return (
                    <a className="flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-xs font-medium text-muted-foreground" href={`#${section.id}`} key={section.id}>
                      <Icon className="h-3.5 w-3.5 text-primary" />
                      {section.label}
                    </a>
                  );
                })}
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              {(Object.keys(versions) as VersionName[]).map((name) => (
                <button
                  className={`rounded-md border px-3 py-2 text-left ${selectedVersion === name ? 'border-primary/40 bg-primary/10 text-primary' : 'border-border bg-card text-foreground'}`}
                  key={name}
                  onClick={() => setSelectedVersion(name)}
                  type="button"
                >
                  <p className="font-serif text-sm font-bold uppercase tracking-wide">{name}</p>
                  <p className="mt-1 truncate text-xs text-muted-foreground">{versions[name].role}</p>
                </button>
              ))}
            </div>
          </section>

          <section className="overflow-hidden rounded-lg border border-border bg-card shadow-sm" id="overview">
            <div className="grid min-h-[360px] lg:grid-cols-[0.95fr_1.05fr]">
              <div className="flex flex-col justify-between border-b border-border bg-muted/20 p-6 lg:border-b-0 lg:border-r">
                <div>
                  <div className="mb-4 flex items-center gap-2 text-primary">
                    <Scale className="h-5 w-5" />
                    <span className="text-xs font-semibold uppercase tracking-[0.24em]">Legal simulation system</span>
                  </div>
                  <h2 className="max-w-xl font-serif text-3xl font-bold uppercase leading-tight tracking-wide text-foreground">
                    Explainable courtroom simulation, bounded by review.
                  </h2>
                  <p className="mt-4 max-w-xl text-sm leading-7 text-muted-foreground">
                    AI Courtroom Harness turns Vietnamese civil-contract disputes into structured evidence, courtroom dialogue, verification surfaces, human review gates, and exportable simulated records.
                  </p>
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  <Metric label="Case type" value="civil contract" />
                  <Metric label="Modes" value="MVP / V1 / V2" />
                  <Metric label="Boundary" value="non-binding" />
                </div>
              </div>

              <CourtroomBlueprint selectedVersion={selectedVersion} onSelect={setSelectedVersion} />
            </div>
          </section>

          <section id="versions">
            <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
              <div className="border-b border-border bg-muted/20 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="mb-1 flex items-center gap-2">
                      <p className="font-serif text-2xl font-bold uppercase tracking-wide text-primary">{selectedVersion}</p>
                      <Badge variant="secondary">{version.status}</Badge>
                    </div>
                    <p className="max-w-2xl text-sm leading-6 text-muted-foreground">{version.promise}</p>
                  </div>
                  <Badge variant="outline" className="mt-1">{version.role}</Badge>
                </div>
              </div>

              <div className="grid gap-0 lg:grid-cols-[1fr_1fr_260px]">
                <VersionColumn title="Product capabilities" icon={CheckCircle2} items={version.features} />
                <VersionColumn title="Technical implementation" icon={BookOpen} items={version.tech} muted />
                <div className="border-t border-border bg-background p-4 lg:border-l lg:border-t-0">
                  <div className="mb-3 flex items-center gap-2 text-primary">
                    <Layers3 className="h-4 w-4" />
                    <h4 className="text-xs font-semibold uppercase tracking-wide">UI surfaces</h4>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {version.surfaces.map((surface) => (
                      <Badge variant="outline" className="bg-muted/30" key={surface}>
                        {surface}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-lg border border-border bg-card shadow-sm" id="flow">
            <div className="flex items-center justify-between gap-3 border-b border-border p-4">
              <div className="flex items-center gap-2 text-primary">
                <Workflow className="h-4 w-4" />
                <h3 className="text-xs font-semibold uppercase tracking-wide">Operational flow</h3>
              </div>
              <Badge variant="outline">single case store</Badge>
            </div>
            <div className="overflow-x-auto p-4 [scrollbar-width:thin] [&::-webkit-scrollbar]:h-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-border">
              <div className="flex min-w-max items-center">
                {flow.map((step, index) => (
                  <div className="flex items-center" key={step}>
                    <div className="flex h-24 w-36 flex-col items-center justify-center rounded-md border border-border bg-background px-3 text-center">
                      <span className="mb-2 flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">{index + 1}</span>
                      <span className="text-xs font-semibold uppercase tracking-wide text-foreground">{step}</span>
                    </div>
                    {index < flow.length - 1 && <div className="h-px w-10 bg-border" />}
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="grid gap-5 lg:grid-cols-[1fr_0.85fr]">
            <div className="rounded-lg border border-border bg-card shadow-sm" id="architecture">
              <div className="border-b border-border p-4">
                <div className="flex items-center gap-2 text-primary">
                  <Layers3 className="h-4 w-4" />
                  <h3 className="text-xs font-semibold uppercase tracking-wide">Architecture swimlane</h3>
                </div>
              </div>
              <div className="divide-y divide-border">
                {architecture.map((layer) => {
                  const Icon = layer.icon;
                  return (
                    <div className="grid gap-3 p-4 sm:grid-cols-[190px_1fr]" key={layer.name}>
                      <div className={`flex items-center gap-3 rounded-md border px-3 py-2 ${layer.tone}`}>
                        <Icon className="h-4 w-4 shrink-0" />
                        <span className="text-xs font-semibold uppercase tracking-wide">{layer.name}</span>
                      </div>
                      <p className="self-center text-sm leading-6 text-muted-foreground">{layer.detail}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="rounded-lg border border-border bg-card shadow-sm" id="safety">
              <div className="border-b border-border p-4">
                <div className="flex items-center gap-2 text-primary">
                  <ShieldCheck className="h-4 w-4" />
                  <h3 className="text-xs font-semibold uppercase tracking-wide">Safety stack</h3>
                </div>
              </div>
              <div className="space-y-3 p-4">
                {guardrails.map(([title, detail], index) => (
                  <div className="relative rounded-md border border-border bg-background p-3" key={title}>
                    <div className="mb-2 flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">{index + 1}</span>
                      <p className="text-sm font-semibold text-foreground">{title}</p>
                    </div>
                    <p className="text-xs leading-5 text-muted-foreground">{detail}</p>
                  </div>
                ))}
                <div className="rounded-md border border-amber-500/20 bg-amber-500/5 p-3">
                  <div className="mb-1 flex items-center gap-2 text-amber-600">
                    <ShieldAlert className="h-4 w-4" />
                    <p className="text-xs font-semibold uppercase tracking-wide">Product boundary</p>
                  </div>
                  <p className="text-sm leading-6 text-muted-foreground">
                    The system can explain and simulate, but it does not issue official judgments or replace legal review.
                  </p>
                </div>
              </div>
            </div>
          </section>
          </main>
        </ScrollArea>
      </div>
    </div>
  );
}

function CourtroomBlueprint({selectedVersion, onSelect}: {selectedVersion: VersionName; onSelect: (version: VersionName) => void}) {
  return (
    <div className="relative min-h-[360px] bg-background p-6">
      <div className="absolute inset-0 opacity-[0.35]" style={{backgroundImage: 'linear-gradient(to right, var(--border) 1px, transparent 1px), linear-gradient(to bottom, var(--border) 1px, transparent 1px)', backgroundSize: '34px 34px'}} />
      <div className="relative z-10 flex h-full min-h-[310px] flex-col justify-between rounded-lg border border-border bg-background/90 p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">Courtroom blueprint</p>
            <p className="mt-1 text-sm text-foreground">One case moves through progressively richer harness layers.</p>
          </div>
          <Badge variant="outline">{selectedVersion} selected</Badge>
        </div>

        <div className="grid items-center gap-4 md:grid-cols-[1fr_120px_1fr]">
          <BlueprintNode title="Case dossier" detail="facts · evidence · claims" icon={FileText} tone="blue" />
          <div className="flex flex-col items-center gap-3">
            <div className="h-px w-full bg-border" />
            <div className="flex h-20 w-20 items-center justify-center rounded-full border border-primary/30 bg-primary/10 text-primary shadow-sm">
              <Scale className="h-8 w-8" />
            </div>
            <div className="h-px w-full bg-border" />
          </div>
          <BlueprintNode title="Simulated record" detail="review · outcome · export" icon={BookOpen} tone="emerald" />
        </div>

        <div className="grid gap-2 sm:grid-cols-3">
          {(Object.keys(versions) as VersionName[]).map((version) => (
            <button
              className={`rounded-md border px-3 py-2 text-left transition-colors ${selectedVersion === version ? 'border-primary/40 bg-primary/10 text-primary' : 'border-border bg-muted/30 hover:bg-muted'}`}
              key={version}
              onClick={() => onSelect(version)}
              type="button"
            >
              <p className="font-serif text-sm font-bold uppercase tracking-wide">{version}</p>
              <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">{versions[version].role}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function BlueprintNode({title, detail, icon: Icon, tone}: {title: string; detail: string; icon: typeof FileText; tone: 'blue' | 'emerald'}) {
  const toneClass = tone === 'blue' ? 'border-blue-500/20 bg-blue-500/5 text-blue-600' : 'border-emerald-500/20 bg-emerald-500/5 text-emerald-600';
  return (
    <div className={`rounded-lg border p-4 ${toneClass}`}>
      <Icon className="mb-4 h-6 w-6" />
      <p className="font-serif text-lg font-bold uppercase tracking-wide text-foreground">{title}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{detail}</p>
    </div>
  );
}

function VersionColumn({title, icon: Icon, items, muted = false}: {title: string; icon: typeof CheckCircle2; items: string[]; muted?: boolean}) {
  return (
    <div className="border-t border-border p-4 lg:border-t-0">
      <div className="mb-3 flex items-center gap-2 text-primary">
        <Icon className="h-4 w-4" />
        <h4 className="text-xs font-semibold uppercase tracking-wide">{title}</h4>
      </div>
      <ul className="space-y-2">
        {items.map((item) => (
          <li className="flex gap-2 text-sm leading-6 text-muted-foreground" key={item}>
            <CheckCircle2 className={`mt-1 h-3.5 w-3.5 shrink-0 ${muted ? 'text-muted-foreground/50' : 'text-primary'}`} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Metric({label, value}: {label: string; value: string}) {
  return (
    <div className="rounded-md border border-border bg-background p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}
