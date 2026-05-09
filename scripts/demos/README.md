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
