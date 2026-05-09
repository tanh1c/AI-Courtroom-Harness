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
