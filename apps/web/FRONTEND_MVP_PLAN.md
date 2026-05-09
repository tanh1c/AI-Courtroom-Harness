# Frontend MVP Plan

This document isolates the remaining `Phase 5` frontend scope for `AI Courtroom Harness`.

## Goal

Build the minimum UI needed to close the MVP from a product perspective.

Backend, retrieval, simulation, review, and report export are already usable. The frontend only needs to expose them clearly and reliably.

## MVP Closure Rule

`Milestone F` can be closed after the UI allows a user to:

1. create a case
2. upload at least one attachment
3. parse the case
4. run the simulation
5. inspect evidence, citations, disputed points, and review flags
6. approve the report in human review
7. open the markdown or HTML report preview

The frontend does **not** need to add automatic judicial verdict generation.

## Recommended Stack

- React + TypeScript
- Vite
- simple CSS modules or plain CSS
- fetch-based API client
- shared types from `packages/shared/types/index.ts`

Do not introduce a heavy design system for the MVP.

## Required Screens

### 1. Case Workspace

Single main page is enough if it contains:

- case creation form
- attachment upload
- parse button
- simulate button
- review approve button
- report preview actions

### 2. Case Detail Panels

The page should visibly contain:

- `Case summary`
- `Evidence table`
- `Legal issues`
- `Claims`
- `Citations`
- `Courtroom transcript`
- `Judge summary`
- `Audit and review`
- `Report preview`

## Recommended Layout

- left column: case input and evidence
- center column: transcript, judge summary, disputed points
- right column: citations, verification, audit, review
- bottom or modal: markdown or HTML report preview

Keep the tone formal, minimal, and document-like.

## API Surface To Use

- `GET /api/v1/cases`
- `POST /api/v1/cases`
- `GET /api/v1/cases/{case_id}`
- `POST /api/v1/cases/{case_id}/attachments`
- `POST /api/v1/cases/{case_id}/parse`
- `GET /api/v1/cases/{case_id}/state`
- `POST /api/v1/cases/{case_id}/simulate`
- `GET /api/v1/cases/{case_id}/audit`
- `POST /api/v1/cases/{case_id}/review`
- `GET /api/v1/reports/{case_id}`
- `POST /api/v1/reports/{case_id}/markdown`
- `GET /api/v1/reports/{case_id}/markdown`

## Suggested Build Order

### FE-0 Foundation

- scaffold `apps/web`
- configure TypeScript
- import shared types
- add API base config
- add a simple app shell

### FE-1 Case Flow

- case list
- create case form
- attachment upload
- parse action
- simulate action

### FE-2 Inspection Panels

- evidence table
- claims list
- citations panel
- disputed points and judge summary
- courtroom transcript
- audit trail and review checklist

### FE-3 Review and Report

- approve review action
- markdown export action
- HTML preview open or embed
- loading, error, empty states

## Panel Requirements

### Evidence Table

Must show:

- `evidence_id`
- type
- source
- status
- excerpt or content summary

### Citations Panel

Must show:

- `citation_id`
- article
- title
- effective status
- accepted or rejected state

### Transcript Panel

Must show ordered turns with:

- stage label
- speaker label
- status
- message

### Review Panel

Must show:

- human review required
- blocked
- reasons
- checklist
- approve action for demo mode

## Acceptance Criteria

- A user can run one full demo case from UI without using the PowerShell demo script.
- Evidence, citations, disputed points, and review flags are visibly inspectable.
- The report preview is reachable from the UI.
- The UI reflects `draft -> parsed -> simulated -> review_required/report_ready`.
- The UI uses shared contracts rather than handwritten incompatible types.

## Non-Goals

- authentication
- multi-user collaboration
- mobile-perfect production UX
- verdict generation
- PDF export

## Handoff Notes For Another AI

- Treat this as a frontend integration task, not a backend redesign.
- Reuse the existing backend flow and shared contracts.
- Keep the UI formal and restrained.
- Prefer closing the MVP quickly over introducing extra abstractions.
