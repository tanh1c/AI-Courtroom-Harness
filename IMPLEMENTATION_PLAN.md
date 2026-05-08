# AI Courtroom Harness Implementation Plan

## 1. Goal

Mục tiêu của bản MVP là xây một hệ thống **legal decision-support and courtroom simulation** cho tiếng Việt, trong đó:

- Hồ sơ vụ án được nhập và chuẩn hóa thành facts, evidence, claims.
- Legal RAG truy xuất điều luật liên quan từ legal corpus.
- Multi-agent flow mô phỏng tranh tụng có cấu trúc.
- Mọi lập luận phải được grounding bằng `evidence_id` và/hoặc `citation_id`.
- Hệ thống có lớp harness để kiểm soát role, verification, logging và human review.

MVP **không** nhằm thay thế thẩm phán hoặc tự động ra quyết định pháp lý chính thức.

## 1.1 Progress Snapshot

- [x] Phase 0 skeleton đã được dựng.
- [x] Shared contracts Python và TypeScript đã được khóa.
- [x] Sample fixtures cho `sample_case_01` đã có.
- [x] Mock API cho create / parse / search / simulate / report đã có.
- [x] Phase 0 đã được đóng hẳn về contract và planning surfaces.
- [x] Legal corpus ingestion baseline đã được scaffold.
- [x] Retrieval pipeline baseline đã bắt đầu với BM25 local seed corpus.
- [x] Internal retrieval baseline eval đã có trên seed corpus.
- [x] Real MVP legal corpus đã được build từ dataset thật.
- [x] Remote vector lane trên Colab đã được validate end-to-end với hybrid retrieval.
- [x] Phase 2 baseline case intake và heuristic parser đã chạy local CPU.
- [x] Attachment metadata parsing và basic PDF text extraction baseline đã có trên local CPU.
- [ ] Multi-agent runtime thật chưa bắt đầu.
- [ ] Guardrails và evaluation suite thật chưa bắt đầu.
- [ ] Frontend workspace thật chưa khởi tạo.

## 2. MVP Scope Freeze

### 2.1 Case Type

Chỉ hỗ trợ một loại case đầu tiên:

- `civil_contract_dispute`

Ví dụ:

- Tranh chấp hợp đồng mua bán tài sản
- Chậm giao hàng
- Chậm thanh toán
- Yêu cầu hoàn tiền / bồi thường

### 2.2 MVP User Journey

```text
Upload / nhập case file
-> Parse hồ sơ
-> Extract facts và evidence
-> Identify legal issues
-> Retrieve legal citations
-> Simulate plaintiff/prosecutor argument
-> Simulate defense argument
-> Run fact-check and citation verification
-> Judge summarizes disputed points
-> Clerk generates report
-> Human review gate
-> Export final markdown report
```

### 2.3 Out of Scope for MVP

- Nhiều loại case phức tạp cùng lúc
- Tự động ra phán quyết cuối cùng
- Fine-tune LLM
- Production-grade auth / RBAC
- Full legal workflow cho cơ quan thật
- Realtime collaboration nhiều người dùng

## 3. Architecture Principles

### 3.1 Product Principles

- Harness-first, không chatbot-first.
- Structured outputs trước, natural-language polish sau.
- Evidence grounding và citation verification là bắt buộc.
- Human review là cổng cuối cho output rủi ro cao.
- Bắt đầu từ một case type hẹp để giảm rủi ro.

### 3.2 Engineering Principles

- Khóa shared contracts sớm để các team làm song song.
- Tách `data plane`, `runtime plane`, `verification plane`, `UI plane`.
- Dùng mock contracts để frontend và agent runtime không phải chờ backend hoàn chỉnh.
- Evaluation và negative tests được xây từ sớm, không để cuối dự án.

## 4. Core Modules

### M1. Shared Domain Contracts

Status:

- [x] Completed for Phase 0

Trách nhiệm:

- Định nghĩa schema dùng chung cho toàn hệ thống.
- Làm source of truth cho API, UI và orchestration.

Schema cần có:

- `Case`
- `Fact`
- `Evidence`
- `LegalIssue`
- `Claim`
- `Citation`
- `AgentTurn`
- `FactCheckResult`
- `CitationVerificationResult`
- `JudgeSummary`
- `TrialMinutes`
- `FinalReport`

Output chính:

- `shared/schemas/*`
- API payload examples
- JSON fixtures cho mock

### M2. Legal Corpus Pipeline

Status:

- [x] Phase 1 usable

Trách nhiệm:

- Load `th1nhng0/vietnamese-legal-documents`
- Clean HTML
- Join metadata + content
- Segment theo article-aware chunking
- Chuẩn hóa metadata hiệu lực văn bản

Output chính:

- Ingestion scripts
- Normalized legal chunks
- Offline build pipeline cho search index

### M3. Retrieval Service

Status:

- [x] Phase 1 usable

Trách nhiệm:

- BM25 search
- Vector search với `mainguyen9/vietlegal-harrier-0.6b`
- Metadata filtering
- Candidate merge
- Optional reranking
- Public retrieval API

Output chính:

- `/legal-search`
- Retrieval service layer
- Top-k citations trả về theo schema chuẩn

### M4. Case Intake and Evidence

Status:

- [x] Phase 2 baseline implemented

Trách nhiệm:

- Nhận text / PDF / pasted case content
- Parse nội dung hồ sơ
- Extract facts
- Extract evidence
- Gán `evidence_id`
- Tạo và cập nhật `case_state`

Output chính:

- Case intake API
- Evidence registry
- Case state manager

### M5. Courtroom Runtime

Status:

- [ ] Not started

Trách nhiệm:

- Điều phối multi-agent flow
- Quản lý turn order
- Enforce role permissions
- Gọi retrieval và verification services

Output chính:

- LangGraph orchestration
- Turn manager
- Runtime state transitions

### M6. Agent Skills

Status:

- [ ] Not started

Trách nhiệm:

- Plaintiff / Prosecutor agent
- Defense agent
- Judge agent
- Clerk agent
- Legal retrieval agent
- Fact-check agent

Yêu cầu:

- Output phải là structured JSON
- Mọi claim phải tham chiếu evidence hoặc citation nếu phù hợp

### M7. Guardrails and Verification

Status:

- [ ] Not started

Trách nhiệm:

- Citation verifier
- Unsupported claim detector
- Contradiction checker
- Outdated legal basis warning
- Human review gate
- Audit logger

Output chính:

- Verification pipeline
- Review checklist
- Audit event store

### M8. Frontend Workspace

Status:

- [ ] Not started

Trách nhiệm:

- Upload / nhập case file
- Evidence panel
- Simulation panel
- Citation panel
- Audit / review panel
- Report preview

Layout đề xuất:

- Left: case file + evidence
- Center: courtroom simulation
- Right: legal citations + verification
- Bottom or drawer: audit log + judge summary

### M9. Reporting and Evaluation

Status:

- [x] Phase 0 report contract and fixture completed

Trách nhiệm:

- Xuất markdown report
- Optional PDF export
- Retrieval benchmark
- Harness negative tests
- Demo cases / seed fixtures

## 5. Shared Contracts to Freeze First

Đây là hạng mục phải làm trước tiên vì mọi lane khác đều phụ thuộc.

### 5.1 Required IDs

- `case_id`
- `fact_id`
- `evidence_id`
- `claim_id`
- `citation_id`
- `turn_id`

### 5.2 Minimal Evidence Schema

```json
{
  "evidence_id": "EVID_001",
  "type": "contract|payment_receipt|message|statement|other",
  "content": "string",
  "source": "string",
  "status": "uncontested|disputed|rejected",
  "used_by": [],
  "challenged_by": []
}
```

### 5.3 Minimal Claim Schema

```json
{
  "claim_id": "CLAIM_001",
  "speaker": "plaintiff_agent",
  "content": "string",
  "evidence_ids": ["EVID_001"],
  "citation_ids": ["LAW_001"],
  "confidence": "low|medium|high"
}
```

### 5.4 Minimal Citation Schema

```json
{
  "citation_id": "LAW_001",
  "doc_id": "12345",
  "title": "string",
  "article": "string",
  "clause": "string",
  "content": "string",
  "retrieval_score": 0.84,
  "effective_status": "active|expired|unknown",
  "source": "vbpl.vn"
}
```

### 5.5 Minimal Turn Schema

```json
{
  "turn_id": "TURN_001",
  "agent": "defense_agent",
  "message": "string",
  "claims": ["CLAIM_001"],
  "evidence_used": ["EVID_001"],
  "citations_used": ["LAW_001"],
  "status": "ok|needs_fact_check|needs_review|rejected"
}
```

### 5.6 Phase 0 API Contract Freeze

#### `POST /api/v1/cases`

Request body:

```json
{
  "title": "Tranh chấp hợp đồng mua bán xe máy",
  "case_type": "civil_contract_dispute",
  "language": "vi",
  "narrative": "string",
  "attachments": []
}
```

Response body:

```json
{
  "case": {
    "case_id": "CASE_001",
    "title": "Tranh chấp hợp đồng mua bán xe máy",
    "case_type": "civil_contract_dispute",
    "language": "vi",
    "status": "draft",
    "attachment_count": 2
  }
}
```

#### `POST /api/v1/cases/{id}/parse`

Response body:

```json
{
  "case": {
    "case_id": "CASE_001",
    "status": "parsed"
  }
}
```

#### `POST /api/v1/cases/{id}/simulate`

Response body:

```json
{
  "case": {
    "case_id": "CASE_001",
    "status": "simulated"
  },
  "final_report": {
    "case_id": "CASE_001"
  }
}
```

#### `POST /api/v1/legal-search`

Response body:

```json
{
  "citations": [],
  "query_strategy": "fixture_stub"
}
```

#### `GET /api/v1/reports/{id}`

Response body:

```json
{
  "case_id": "CASE_001",
  "report_status": "report_ready",
  "generated_from_turns": ["TURN_001", "TURN_002"],
  "report": {
    "case_id": "CASE_001"
  }
}
```

## 6. Phase Plan

## Phase 0. Foundation and Freeze

Mục tiêu:

- Chốt phạm vi MVP.
- Khóa shared schema và API contract.
- Dựng skeleton repo và dev workflow.

Tasks:

- [x] Tạo cấu trúc repo theo module.
- [x] Định nghĩa shared schemas bằng Pydantic và TypeScript types.
- [x] Tạo fixtures cho `sample_case_01`.
- [x] Viết API contract draft đầy đủ cho:
  - [x] `/cases`
  - [x] `/cases/{id}/parse` ở mức mock shape
  - [x] `/cases/{id}/simulate` ở mức mock shape
  - [x] `/legal-search` ở mức mock shape
  - [x] `/reports/{id}`
- [x] Chốt naming convention cho IDs và statuses.
- [x] Thêm bảng lane owner/status để kickoff song song có cấu trúc.

Deliverables:

- [x] `IMPLEMENTATION_PLAN.md`
- [x] `shared contracts`
- [x] `sample fixtures`
- [x] `repo skeleton`

Acceptance criteria:

- [x] Frontend, backend và orchestration đều đọc được cùng một schema.
- [x] Có mock JSON đủ để FE dựng UI không cần backend thật.
- [x] Có 1 case mẫu hoàn chỉnh end-to-end ở mức data.
- [x] Các planning surfaces đủ rõ để assign lane và bắt đầu Phase 1.

## Phase 1. Data and Retrieval Plane

Mục tiêu:

- Hoàn thành Legal RAG nền tảng cho MVP.

Tasks:

- [x] Load dataset `th1nhng0/vietnamese-legal-documents` trên corpus thật.
- [x] Clean HTML content.
- [x] Join metadata và content trong ingest pipeline.
- [x] Chunk theo article-aware segmentation.
- [x] Xây BM25 index.
- [x] Xây vector index bằng `mainguyen9/vietlegal-harrier-0.6b` và validate remote Colab lane.
- [x] Thêm metadata filters cho hiệu lực và lĩnh vực.
- [x] Expose `/legal-search` bằng retrieval baseline thật.

Deliverables:

- [x] Corpus ingestion pipeline
- [x] Search indexes
- [x] Retrieval API
- [x] Top-k result schema

Acceptance criteria:

- [x] Query legal issue trả được top 3-5 passages hợp lý trên seed corpus baseline.
- [x] Mỗi result có `citation_id`, metadata và trạng thái hiệu lực.
- [x] Có benchmark baseline ban đầu trên một tập query nhỏ nội bộ.
- [x] Hybrid retrieval chạy end-to-end với BM25 local + vector remote trên Colab.

## Phase 2. Case Intelligence Plane

Mục tiêu:

- Chuẩn hóa đầu vào hồ sơ thành structured case state.

Tasks:

- [x] Xây case input API.
- [x] Parse case text / PDF cơ bản.
- [x] Extract facts.
- [x] Extract evidence.
- [x] Assign `evidence_id`.
- [ ] Lưu vào database.
- [x] Thêm GET endpoints cho frontend lấy draft và parsed state.
- [ ] Hiển thị evidence table.

Deliverables:

- [x] Case intake API
- [x] Evidence registry
- [x] Case state manager
- [x] Sample parsed case view ở mức fixture

Acceptance criteria:

- [x] Một case mẫu được parse thành facts và evidence có thể kiểm tra lại.
- [x] Evidence có source rõ ràng.
- [x] `case_state` có thể được truyền thẳng sang orchestration.

## Phase 3. Courtroom Simulation Plane

Mục tiêu:

- Chạy được luồng tranh tụng đa agent có cấu trúc.

Tasks:

- [ ] Xây LangGraph flow.
- [ ] Xây Plaintiff / Prosecutor agent.
- [ ] Xây Defense agent.
- [ ] Xây Judge agent.
- [ ] Xây Clerk agent.
- [ ] Xây Legal Retrieval agent.
- [ ] Enforce turn order và role permissions cơ bản.

Deliverables:

- [ ] Working simulation runtime
- [x] Structured agent outputs ở mức fixture/schema
- [x] Trial minutes draft ở mức fixture

Acceptance criteria:

- [ ] Chạy được flow đầy đủ trên case mẫu.
- [x] Agent outputs không phải free-form hoàn toàn, mà bám schema.
- [x] Mỗi claim quan trọng có evidence hoặc citation đi kèm trong fixture mẫu.

## Phase 4. Harness and Safety Plane

Mục tiêu:

- Thêm lớp kiểm soát và verification để hệ thống đáng tin hơn.

Tasks:

- [ ] Xây Citation Verifier.
- [ ] Xây Unsupported Claim Detector.
- [ ] Xây Contradiction Checker.
- [ ] Xây Outdated Legal Basis Warning.
- [ ] Xây Audit Logger.
- [ ] Xây Human Review Gate.

Deliverables:

- [x] Verification reports ở mức fixture
- [ ] Audit trail
- [x] Review checklist ở mức fixture

Acceptance criteria:

- [ ] Citation không tồn tại trong retrieved set bị reject.
- [ ] Claim không có evidence bị flag.
- [ ] Citation hết hiệu lực bị warning.
- [ ] Case rủi ro cao bị chặn ở human review gate.

## Phase 5. Productization and Demo

Mục tiêu:

- Biến hệ thống thành MVP demo hoàn chỉnh.

Tasks:

- [ ] Hoàn thiện UI panels.
- [ ] Thêm report preview.
- [ ] Export markdown report.
- [ ] Optional PDF export.
- [x] Seed demo cases.
- [ ] Viết smoke tests và demo script.

Deliverables:

- [ ] Demo-ready app
- [x] Final report template ở mức fixture structure
- [x] Demo dataset / fixtures
- [ ] Smoke test checklist

Acceptance criteria:

- [ ] Có thể demo từ upload case đến final report.
- [ ] UI hiển thị rõ evidence, citations, disputed points và review flags.
- [x] Có ít nhất 1 demo case ổn định để quay video hoặc thuyết trình ở mức data fixture.

## 7. Parallel Work Lanes

### 7.1 Lane Owner and Status Table

| Lane | Scope | Initial owner role | Current status | Phase 1 readiness |
| --- | --- | --- | --- | --- |
| Lane A | Data and Retrieval | Data/RAG engineer | Phase 1 usable | Completed |
| Lane B | Backend Domain | Backend/platform engineer | Phase 0 completed | Ready now |
| Lane C | Agent Runtime | Agent/runtime engineer | Planned with mock contracts | Ready now |
| Lane D | Safety and Evaluation | Safety/eval engineer | Planned with fixtures | Ready now |
| Lane E | Frontend | Frontend engineer | Planned with shared types | Ready now |

## Lane A. Data and Retrieval

Sở hữu:

- `M2`
- `M3`

Công việc chính:

- Ingestion
- Chunking
- Indexing
- Retrieval API

Phụ thuộc:

- Chỉ cần `M1` contracts

## Lane B. Backend Domain

Sở hữu:

- `M1`
- `M4`

Công việc chính:

- Shared schemas
- Case intake
- Evidence registry
- Case state persistence

Phụ thuộc:

- Ít phụ thuộc, nên bắt đầu sớm nhất

## Lane C. Agent Runtime

Sở hữu:

- `M5`
- `M6`

Công việc chính:

- LangGraph
- Agent prompts
- Turn manager
- Structured outputs

Phụ thuộc:

- Cần `M1`
- Có thể dùng retrieval mock trước khi `M3` xong

## Lane D. Safety and Evaluation

Sở hữu:

- `M7`
- `M9`

Công việc chính:

- Verifier
- Fact-check rules
- Audit events
- Negative tests
- Eval harness

Phụ thuộc:

- Cần `M1`
- Có thể dùng fixtures và simulated turns để làm sớm

## Lane E. Frontend

Sở hữu:

- `M8`

Công việc chính:

- Workspace UI
- Panels
- Report preview
- Review experience

Phụ thuộc:

- Chỉ cần mock contracts từ `M1`

## 8. Recommended Sequence for Team Kickoff

### Week 0

- Lane B chốt `M1`
- Lane E dựng UI từ mock
- Lane A dựng legal ingestion skeleton
- Lane C dựng orchestration skeleton
- Lane D viết test fixtures và negative cases

### Week 1

- Lane A hoàn thành retrieval baseline
- Lane B hoàn thành case intake baseline
- Lane C nối runtime với mock retrieval
- Lane E render case/evidence/citation panels
- Lane D dựng citation/evidence validation rules

### Week 2

- Thay mock retrieval bằng retrieval thật
- Nối case intake thật vào simulation
- Thêm judge summary, clerk minutes
- Thêm audit logs và review flags

### Week 3

- End-to-end integration
- Demo case stabilization
- Report export
- Smoke tests

## 9. Milestones

- [x] `Milestone A`: Shared contracts freeze
- [x] `Milestone B`: Legal retrieval usable
- [ ] `Milestone C`: Case ingestion usable
- [ ] `Milestone D`: Structured simulation usable
- [ ] `Milestone E`: Safety gate enforced
- [ ] `Milestone F`: Demo-ready MVP

## 10. Repo Structure Suggestion

```text
ai-court/
  apps/
    api/
    web/
  packages/
    shared/
      schemas/
      fixtures/
      constants/
    retrieval/
    orchestration/
    verification/
    reporting/
  data/
    raw/
    processed/
    indexes/
  scripts/
    ingest/
    eval/
    demos/
  docs/
    architecture/
    prompts/
    eval/
```

## 11. Key Risks and Mitigations

### Risk 1. Scope quá rộng

Mitigation:

- Chỉ làm `civil_contract_dispute` cho MVP.
- Không ôm nhiều loại vụ án ngay.

### Risk 2. RAG tốt nhưng agent vẫn hallucinate

Mitigation:

- Enforce structured outputs.
- Reject citation không nằm trong retrieved set.
- Tách claim khỏi narration.

### Risk 3. FE bị chờ backend

Mitigation:

- Freeze contracts sớm.
- Mock everything từ Phase 0.

### Risk 4. Legal corpus noisy hoặc outdated

Mitigation:

- Luôn hiển thị `effective_status`.
- Cảnh báo snapshot và yêu cầu human review khi cần.

### Risk 5. Orchestration phức tạp quá sớm

Mitigation:

- Bắt đầu bằng flow tuyến tính trước.
- Chỉ thêm branching khi baseline đã ổn định.

## 12. Definition of Done for MVP

MVP được xem là hoàn thành khi:

- User nhập hoặc upload được một case dân sự đơn giản.
- Hệ thống extract được facts và evidence có ID rõ ràng.
- Hệ thống retrieve được legal citations liên quan.
- Multi-agent simulation chạy end-to-end.
- Unsupported claims và invalid citations bị flag hoặc reject.
- Judge summary và clerk report được sinh ra theo format chuẩn.
- Có human review checklist trước output cuối.
- Có ít nhất 1 demo case ổn định để trình bày.

## 13. Immediate Next Tasks

1. [x] Tạo repo skeleton theo module.
2. [x] Định nghĩa `shared schemas` bằng Pydantic và TypeScript.
3. [x] Tạo `sample_case_01.json` và fixtures liên quan.
4. [x] Chốt API contracts cho `cases`, `legal-search`, `simulate`, `reports`.
5. [x] Chia owner cho từng lane và bắt đầu Phase 0.
