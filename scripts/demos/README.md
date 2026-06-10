# Demo Scripts

## Production-readiness check

Before a portfolio demo, run the local readiness gate from the repo root:

```powershell
npm run demo:ready
npm run smoke
npm run typecheck
npm run build:web
```

What it verifies:

- API imports and health route work through FastAPI `TestClient`
- legal search returns citations from the local retrieval stack
- prompt-injection guardrails block unsafe search input
- case parse, simulation, human review, EvalOps, and printable export work end-to-end
- smoke tests cover security, retrieval, EvalOps, and report export regressions
- frontend TypeScript and production build pass

To run the API and frontend manually for the browser demo:

```powershell
npm run serve:api
npm run dev:web
```

Run the scripted MVP demo from the repo root:

```powershell
.\scripts\demos\run_demo.ps1
```

Optional browser preview:

```powershell
.\scripts\demos\run_demo.ps1 -OpenPreview
```

What it does:

- creates a demo case
- uploads a sample PDF attachment
- parses facts and evidence
- runs the courtroom simulation
- approves human review
- exports the markdown report
- generates `report_preview.html` next to the markdown export

Notes:

- You do not need to start `uvicorn` in another terminal for this scripted demo.
- If `AI_COURT_VECTOR_API_URL` is configured and the Colab/ngrok tunnel is still live, the demo
  uses hybrid retrieval automatically.
- If the Colab vector server is offline, the demo still runs with local BM25 retrieval.

## V2 Full Trial Demo

Generate a realistic PDF evidence bundle and run the stage-by-stage V2 trial:

```powershell
.\.venv\Scripts\python.exe scripts\demos\run_v2_full_trial_demo.py
```

This creates PDFs under `data/raw/demo_evidence/full_contract_breach/`, uploads them through the
API test client, parses PDF text, runs the full simulated trial, and exports `hearing_v2_record.md`
plus `hearing_v2_record.html`.

To let the configured LLM polish high-value V2 dialogue turns, for example with DeepSeek:

```powershell
.\.venv\Scripts\python.exe scripts\demos\run_v2_full_trial_demo.py --use-llm --llm-provider deepseek --llm-max-turns 13
```

The LLM layer is bounded and guarded: evidence-reading stays deterministic, official-judgment
language is blocked, claim grounding is verified against related evidence/citations, and the
runtime falls back to deterministic text if the provider fails or introduces unsupported claims.

To generate only the PDF evidence bundle:

```powershell
.\.venv\Scripts\python.exe scripts\demos\generate_v2_evidence_bundle.py
```
