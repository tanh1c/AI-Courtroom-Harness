# AI Prompt FE Handoff

Status: superseded. The frontend lane has been implemented in `frontend/` with `MVP | V1 | V2` modes. Keep this file only as historical handoff context.

Use this prompt with a frontend coding agent:

```text
Read `apps/web/FRONTEND_MVP_PLAN.md` first, then implement the MVP frontend in `apps/web`.

Constraints:
- Do not redesign the product scope or backend contracts.
- Reuse existing APIs from `apps/api` and shared types from `packages/shared/types/index.ts`.
- Build only the remaining frontend needed to close Milestone F.
- Keep the UI formal, minimal, document-like, and suitable for a legal workflow.
- Do not add authentication, PDF export, verdict generation, or heavy UI frameworks.

Required outcome:
- A user can create a case, upload an attachment, parse, simulate, inspect evidence/citations/disputed points/review flags, approve review, and open the report preview from the UI.

Implementation order:
1. Scaffold React + TypeScript + Vite in `apps/web`
2. Build the case workspace and API wiring
3. Build evidence, citations, transcript, judge summary, audit, and review panels
4. Add report preview access and final loading/error states

Before finishing:
- run the frontend locally
- verify the full flow against the existing backend
- update `apps/web/README.md`
- commit and push your work
```
