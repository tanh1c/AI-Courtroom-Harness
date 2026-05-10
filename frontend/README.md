# AI Courtroom Frontend

Mock courtroom UI wired to the backend V2 trial pipeline.

## Run Locally

From the repository root:

```powershell
npm run dev:api
npm run dev:web
```

The Vite dev server proxies `/api/*` and `/health` to `http://127.0.0.1:8000` by default.
Override with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## V2 Pipeline

The UI can:

- Load existing cases from `GET /api/v1/cases`.
- Create a case and upload PDF attachments.
- Run parse -> V2 start -> V2 stage advances -> markdown/html export.
- Render `GET /api/v1/cases/{case_id}/trial-v2/ui-state`.
