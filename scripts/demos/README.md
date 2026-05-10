# Demo Scripts

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

To generate only the PDF evidence bundle:

```powershell
.\.venv\Scripts\python.exe scripts\demos\generate_v2_evidence_bundle.py
```
