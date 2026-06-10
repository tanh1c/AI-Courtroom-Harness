Dưới đây là shortlist theo hướng **repo để học architecture production-grade**, không phải chỉ “library để import”. Stars/activity/license là snapshot theo GitHub/web ở thời điểm mình kiểm tra hôm nay; trước khi dùng thật nên kiểm tra lại `LICENSE`, model-weight license và dependency license.

**Legend:** `P` = production readiness, `R` = relevance với AI Courtroom Harness.

---

## 1. PDF / OCR / document ingestion

**Primary nên học:** Docling + OCRmyPDF.
**Fallback:** Unstructured nếu cần connector/ETL rộng; Marker/Surya để học layout-aware OCR nhưng phải kiểm tra license.

| Repo                             | Stars/activity/license                                                                                                                                       | Vì sao đáng học + file/folder nên đọc                                                                                                   | Pattern nên borrow                                                                  | Không nên copy                                                                | P/R |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | --- |
| **docling-project/docling**      | ~61.2k★, active release Jun 8 2026, MIT; tập trung parse tài liệu sang structured representation, layout/table, tích hợp LangChain/LlamaIndex. ([GitHub][1]) | Đọc `docling/document_converter.py`, `docling/pipeline/`, `docling/datamodel/`, `docs/examples/`, `tests/`.                             | Tạo **canonical document object**: page, block, table, bbox, provenance.            | Đừng khóa toàn bộ system vào một parser duy nhất.                             | 5/5 |
| **Unstructured-IO/unstructured** | Apache-style OSS, Docker images, nhiều partitioner cho PDF/HTML/Word và workflow LLM. ([GitHub][2])                                                          | Đọc `unstructured/partition/`, `unstructured/partition/pdf.py`, `unstructured/chunking/`, `unstructured/ingest/`, `test_unstructured/`. | Tách `partition -> clean -> chunk -> metadata -> index`.                            | Không dùng như black box; chất lượng PDF pháp lý cần eval riêng.              | 4/5 |
| **ocrmypdf/OCRmyPDF**            | ~33.8k★, active v17.4.1 Apr 2026, MPL-2.0; battle-tested OCR text layer, deskew, PDF/A, plugin support. ([GitHub][3])                                        | Đọc `src/ocrmypdf/_pipeline.py`, `src/ocrmypdf/pluginspec.py`, `tests/`, Docker setup.                                                  | OCR như **background job idempotent**, lưu output artifact + confidence/provenance. | Đừng coi OCR text là ground truth trong legal workflow.                       | 5/4 |
| **PaddlePaddle/PaddleOCR**       | 70k+★, Apache-2.0, active; hỗ trợ OCR, structure extraction, JSON/Markdown LLM-ready. ([GitHub][4])                                                          | Đọc `paddleocr/`, `ppstructure/`, `tools/infer/`, `deploy/`, `test_tipc/`.                                                              | Layout + table extraction pipeline cho scanned evidence.                            | Kiểm tra dependency license, đặc biệt các lib PDF/OCR phụ thuộc.              | 4/4 |
| **datalab-to/marker**            | ~35.9k★, GPL-3.0 code; rất mạnh PDF/image/PPTX/DOCX → markdown/JSON/chunks, nhưng có commercial/license caveat. ([GitHub][5])                                | Đọc `marker/converters/pdf.py`, `marker/`, `benchmarks/`, `examples/`, `tests/`.                                                        | Output `chunks` có page/block/table structure; benchmark parser quality.            | Không copy/use trong product commercial nếu chưa rõ GPL/model-weight license. | 3/5 |
| **datalab-to/surya**             | Code Apache-2.0 nhưng model weights có license riêng; OCR 90+ languages, layout/table recognition. ([GitHub][6])                                             | Đọc `surya/recognition/`, `surya/layout/`, `surya/table_rec/`, `surya/settings.py`.                                                     | Layout-aware OCR cho evidence scan, table block, reading order.                     | Đừng assume benchmark generalize sang tài liệu legal scan kém chất lượng.     | 3/4 |

---

## 2. RAG / retrieval / hybrid search

**Primary nên học:** Vespa sample-apps cho hybrid ranking, Haystack/LlamaIndex cho pipeline, Qdrant cho vector DB thực dụng.

| Repo                            | Stars/activity/license                                                                                          | Vì sao đáng học + file/folder nên đọc                                                         | Pattern áp dụng cho legal RAG                                                | Không nên copy                                              | P/R |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------- | --- |
| **vespa-engine/sample-apps**    | Repo sample production-ish; có hybrid, BM25, vector, ColBERT, RAG blueprint, GitHub Actions. ([GitHub][7])      | Đọc `simple-hybrid-search/`, `msmarco-ranking/`, `rag-blueprint/`, `.github/`.                | **BM25 + dense + rerank + RRF/ColBERT** cho legal retrieval.                 | Vespa hơi nặng nếu portfolio nhỏ; đừng over-engineer infra. | 5/5 |
| **deepset-ai/haystack**         | Framework Python production-ready cho modular RAG pipelines, retrieval/routing/memory/generation. ([GitHub][8]) | Đọc `haystack/components/retrievers/`, `document_stores/`, `pipelines/`, `tests/`.            | Pipeline rõ ràng: retriever, reranker, prompt builder, generator, evaluator. | Đừng biến pipeline thành YAML quá khó debug.                | 4/5 |
| **qdrant/qdrant**               | Apache-2.0, Rust vector DB, production-ready API, payload filtering/faceted search. ([GitHub][9])               | Đọc `lib/collection/`, `lib/segment/`, `openapi/`, `qdrant-client`, `qdrant/examples`.        | Metadata filtering theo `case_id`, `jurisdiction`, `doc_type`, `page_range`. | Đừng chỉ dùng dense retrieval; legal cần keyword + filter.  | 5/4 |
| **run-llama/llama_index**       | MIT, 300+ integrations, ingestion/index/retrieval/query interfaces. ([GitHub][10])                              | Đọc `llama-index-core/.../retrievers`, `indices`, `query_engine`, `docs/examples/evaluation`. | Node/source attribution, ingestion pipeline nhanh cho prototype.             | Tránh “magic abstraction” ở core production path.           | 4/5 |
| **langchain-ai/langchain**      | MIT, ecosystem lớn; standard interfaces cho models/embeddings/vector stores/retrievers. ([GitHub][11])          | Đọc `libs/langchain/langchain/retrievers/`, `libs/community/...`, `templates/rag-*`.          | Loader/retriever/tool abstraction; integration tests.                        | Đừng copy chain spaghetti khó trace.                        | 4/4 |
| **FlagOpen/FlagEmbedding**      | Active BGE/FlagEmbedding; BGE-M3 hỗ trợ dense/sparse/multi-vector, 100+ languages, 8192 tokens. ([GitHub][12])  | Đọc `FlagEmbedding/`, `research/`, examples reranker.                                         | Embedding + reranker experiment harness cho legal corpus.                    | Đừng fine-tune nếu chưa có eval dataset tốt.                | 3/5 |
| **beir-cellar/beir**            | Benchmark IR đa domain; framework chung để eval retrieval models. ([GitHub][13])                                | Đọc `beir/retrieval/`, `examples/`, wiki install/eval.                                        | Offline retrieval benchmark: recall@k, nDCG, MRR cho legal QA.               | BEIR dataset không thay thế legal eval riêng.               | 3/4 |
| **stanford-futuredata/ColBERT** | Late-interaction retrieval research code; hữu ích để hiểu MaxSim/rerank.                                        | Đọc `colbert/`, indexing/search examples.                                                     | Late interaction reranking cho câu hỏi pháp lý dài.                          | Không nên ship ngay nếu chưa tối ưu latency/cost.           | 2/4 |

---

## 3. Agent orchestration / graph runtime

**Primary:** LangGraph cho courtroom workflow.
**Durable workflow:** Temporal.
**Typed agent layer:** PydanticAI hoặc OpenAI Agents SDK.

| Repo                                                                   | Stats/license/activity                                                                                                                              | Architecture pattern nên học         | File/folder nên inspect                                                         | Test/tool/state pattern                                    | Không nên copy                                                  | P/R |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------- | --- |
| **langchain-ai/langgraph**                                             | MIT; nhấn mạnh stateful, long-running agents, durable execution, human-in-the-loop, memory. ([GitHub][14])                                          | State machine / graph runtime.       | `libs/langgraph/langgraph/graph/`, `checkpoint/`, `prebuilt/`, `tests/`.        | `CaseState`, checkpoint, retry edge, human approval node.  | Không biến mọi thứ thành agent; nhiều bước nên deterministic.   | 5/5 |
| **pydantic/pydantic-ai**                                               | Python agent framework cho production GenAI app, typed outputs/tooling. ([GitHub][15])                                                              | Type-safe agent + structured output. | `pydantic_ai/`, examples, eval examples.                                        | Pydantic schema cho legal findings, citations, objections. | Không để model tự quyết schema quan trọng.                      | 4/5 |
| **openai/openai-agents-python**                                        | Lightweight multi-agent workflows, tools, handoffs, tracing; active release May 2026. ([GitHub][16])                                                | Agents + tools + handoff + trace.    | `src/agents/`, `examples/`, tests.                                              | Good cho agent step trace trong inspection UI.             | Nếu muốn vendor-neutral tuyệt đối thì wrap lại interface.       | 4/4 |
| **temporalio/samples-python / temporal-community/openai-agents-demos** | Temporal cho durable long-running workflows; demo AI agents + human-in-loop. ([GitHub][17])                                                         | Workflow orchestration ngoài LLM.    | `workflows/`, `activities/`, AI agent demos.                                    | Retry, timeout, compensation cho ingestion/eval jobs.      | Không dùng Temporal cho mọi request sync.                       | 5/4 |
| **microsoft/semantic-kernel / microsoft/agent-framework**              | SK đang hướng sang Microsoft Agent Framework; hỗ trợ plugins, process framework, vector DB, enterprise. ([GitHub][18])                              | Plugin/process abstraction.          | `python/semantic_kernel/agents/`, `functions/`, `processes/`.                   | Tool registry + planner boundaries.                        | Có thể hơi enterprise/.NET-heavy cho portfolio Python.          | 4/3 |
| **crewAIInc/crewAI**                                                   | Crews + Flows; event-driven workflow/state/branching. ([GitHub][19])                                                                                | Role-based crew + flow layer.        | `src/crewai/`, `flow/`, `tests/`, examples.                                     | Học UX/DSL cho workflow.                                   | Đừng copy role-play multi-agent nếu graph deterministic đủ tốt. | 3/3 |
| **microsoft/autogen**                                                  | Quan trọng: repo AutoGen hiện báo maintenance mode và khuyên user mới dùng Microsoft Agent Framework; Studio không production-ready. ([GitHub][20]) | Study-only multi-agent conversation. | `python/packages/autogen-core/`, `agentchat/`, `autogen_ext/`, `autogenbench/`. | Học message protocol, agent tool wrapping.                 | Không chọn làm nền chính cho project mới.                       | 2/3 |

---

## 4. Evaluation harness cho LLM / RAG / agents

**Primary:** DeepEval + RAGAS + Promptfoo + Phoenix/Langfuse.
**Fallback nghiên cứu:** OpenAI Evals, Inspect AI.

| Repo                            | Stats/license/activity                                                                                          | Eval design đáng học                   | File/folder inspect                                            | Metrics/report/CI pattern                                              | Không nên copy                                          | P/R |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------- | --- |
| **confident-ai/deepeval**       | Apache-2.0; Pytest-like LLM eval; có RAG metrics, hallucination, agentic metrics. ([GitHub][21])                | Unit/regression tests cho LLM output.  | `deepeval/metrics/`, `test_case/`, `integrations/`, `tests/`.  | `pytest` CI: faithfulness, context precision/recall, tool correctness. | LLM-as-judge phải có calibration set.                   | 4/5 |
| **vibrantlabsai/ragas**         | Apache; RAG eval + testset generation + feedback loop. ([GitHub][22])                                           | Reference-free RAG eval.               | `src/ragas/metrics/`, `testset/`, examples.                    | Retrieval-focused context metrics + faithful generation.               | Không chỉ dùng synthetic questions.                     | 4/5 |
| **promptfoo/promptfoo**         | MIT; CLI/library eval + red teaming, CI/CD, custom providers. ([GitHub][23])                                    | YAML eval matrix.                      | `src/`, `examples/`, `promptfooconfig.yaml`, redteam examples. | Prompt/model/version comparison, JSON/HTML reports, CI gate.           | Đừng chỉ test prompt; test full RAG API.                | 4/4 |
| **Arize Phoenix**               | Tracing, evaluation, datasets, experiments, playground, prompt management; OpenTelemetry-based. ([GitHub][24])  | Trace → dataset → experiment loop.     | `src/phoenix/`, evals, datasets, UI.                           | Convert failed traces thành eval cases.                                | Không thay thế unit tests bằng dashboard.               | 4/4 |
| **TruLens**                     | MIT; RAG Triad, feedback functions, OpenTelemetry tracing, agent metrics. ([GitHub][25])                        | Feedback functions attached to traces. | `src/trulens/`, `examples/`, dashboard, tests.                 | Groundedness, answer relevance, context relevance.                     | Judge scores không nên là single source of truth.       | 4/4 |
| **openai/evals**                | Registry + framework; YAML templates, Snowflake logging, examples. ([GitHub][26])                               | Eval registry as code.                 | `evals/registry/`, `examples/`, `docs/`, `tests/unit/evals/`.  | JSONL-style run records, eval versioning.                              | Một số patterns có thể cũ; adapt chứ không copy nguyên. | 3/4 |
| **UKGovernmentBEIS/inspect_ai** | MIT; UK AISI framework cho LLM evals, prompt engineering, tools, multi-turn, model-graded evals. ([GitHub][27]) | `Task -> Solver -> Scorer`.            | `inspect_ai/`, `examples/`, `inspect_evals`.                   | Reproducible agent/tool evals, sandboxed tasks.                        | Hơi research-oriented nếu chỉ cần simple CI.            | 4/4 |
| **evidentlyai/evidently**       | OSS Python lib; eval/test/monitor ML & LLM systems, 100+ metrics, offline/live monitoring. ([GitHub][28])       | Monitoring + eval reports.             | `src/evidently/`, examples, reports.                           | Drift, quality, LLM judge dashboards.                                  | Không dùng dashboard thay cho legal-specific rubric.    | 4/3 |

---

## 5. Observability / tracing cho AI apps

**Primary:** Langfuse nếu muốn full UI self-host; Phoenix nếu muốn OTEL/eval loop; Helicone nếu cần gateway/cost tracking.

| Repo                                    | Stats/license/activity                                                                                                    | Integration pattern                                    | Backend/schema/UI nên học                                       | Không nên copy                                                          | P/R |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------- | --- |
| **langfuse/langfuse**                   | Open-source LLM engineering platform: traces, prompt mgmt, evals, datasets, playground; Docker/K8s/Helm. ([GitHub][29])   | SDK instrumentation around LLM/tool/retrieval calls.   | Trace model: session, observation, prompt, score, dataset item. | Đừng log raw legal/PII text nếu chưa redact.                            | 5/5 |
| **Arize Phoenix**                       | Vendor-agnostic tracing/eval/datasets/experiments, OpenTelemetry-based, Docker/K8s. ([GitHub][24])                        | OTEL spans cho retriever, reranker, LLM, verifier.     | UI trace tree + eval dataset workflow.                          | Không phụ thuộc dashboard để enforce safety.                            | 4/4 |
| **Helicone**                            | Gateway/logging, cost/latency, prompt mgmt; architecture gồm Web/Worker/Supabase/ClickHouse/Minio; Apache. ([GitHub][30]) | LLM gateway proxy.                                     | Cost/token/latency schema, request replay UI.                   | Gateway chỉ thấy LLM call, không đủ graph state nếu không custom spans. | 4/4 |
| **traceloop/openllmetry**               | OpenLLMetry = extensions trên OpenTelemetry, Apache-2.0, kết nối Datadog/Honeycomb/etc. ([GitHub][31])                    | Non-intrusive tracing cho LangChain/LlamaIndex/OpenAI. | Instrumentors + semantic conventions.                           | Đừng trace sensitive prompts without redaction.                         | 4/4 |
| **open-telemetry/opentelemetry-python** | Reference OTEL Python SDK/API, Apache-2.0. ([GitHub][32])                                                                 | Custom spans trong FastAPI + AI services.              | `opentelemetry-api`, `opentelemetry-sdk`, examples.             | Raw OTEL không có AI-specific UX; cần Langfuse/Phoenix/collector.       | 5/3 |
| **mlflow/mlflow**                       | LLM/agent observability, tracing, eval, model registry, OpenTelemetry/MCP integration. ([GitHub][33])                     | Experiment + trace + model/prompt registry.            | Tracking server, eval APIs, prompt/version registry.            | Hơi ML-platform heavy nếu chỉ cần app traces.                           | 4/3 |

---

## 6. Human review / annotation / audit workflow

**Primary:** Label Studio nếu cần review UI mạnh; Argilla nếu cần feedback/data curation; tự build audit table cho legal decisions.

| Repo | Stats/license/activity | Workflow/data model nên học | File/folder inspect | Adapt cho legal AI review | Không nên copy | P/R |
|---|---|---|---|---|---|
| **HumanSignal/label-studio** | ~28k★, Apache-2.0, updated Jun 9 2026; multi-type labeling UI, Docker/Compose/Postgres options. ([GitHub][34]) | Project/task/annotation/reviewer workflow. | `label_studio/`, frontend, `docker-compose`, `tests/`. | Review queue: answer, evidence spans, citation correctness, approve/reject. | UI quá lớn; không embed nguyên nếu chỉ cần lightweight review. | 5/4 |
| **argilla-io/argilla** | ~5k★, Apache-2.0; mature/stable nhưng maintainers nói không thêm feature mới, chỉ bugfix/patch. ([GitHub][35]) | Human feedback + semantic search + data iteration. | `argilla-server/`, `argilla-frontend/`, `argilla/`, examples. | Collect expert feedback cho legal answer quality, issue tags. | Không chọn nếu cần roadmap feature active lâu dài. | 3/5 |
| **doccano/doccano** | ~11k★, MIT, updated Apr 2026; text classification/NER/seq2seq annotation. ([GitHub][36]) | Simple text annotation workflow. | Django backend, Vue/Nuxt frontend, REST API, `doccano-client`. | Annotate legal entities, claims, issue categories. | Không đủ cho complex document/citation review UI. | 3/3 |
| **HumanSignal/label-studio-ml-backend** | ~1.1k★, Apache-2.0, updated May 2026; ML backend boilerplates. ([GitHub][37]) | Pre-labeling + active learning loop. | ML backend templates, API handlers. | Auto-suggest citation correctness labels, human confirms. | Không để model auto-approve legal outputs. | 3/4 |
| **Langfuse** | Datasets/evals/score traces. ([GitHub][29]) | Human score attached to trace/run. | Score/dataset APIs, UI. | Reviewer records: `faithful`, `citation_valid`, `needs_lawyer_review`. | Không dùng score-only nếu cần full legal audit trail. | 4/4 |
| **Phoenix** | Datasets/experiments/traces. ([GitHub][24]) | Review failed traces → eval dataset. | Dataset/eval UI. | Convert bad courtroom simulations into regression evals. | Không đủ approval workflow nếu cần role-based review. | 4/4 |

---

## 7. Full-stack AI product reference repos

**Primary để học UI/backend/deploy:** Azure Search OpenAI Demo + RAGFlow + Dify/Open WebUI.
**Dùng cho portfolio:** học patterns, không copy product identity.

| Repo | Stats/license/activity | Architecture/folder nên học | Deployment/testing | UI/UX pattern đáng copy conceptually | Không nên copy | P/R |
|---|---|---|---|---|---|
| **Azure-Samples/azure-search-openai-demo** | ~7.7k★, MIT, release Apr 2026; RAG chat over docs, citations, thought process, UI settings. ([GitHub][38]) | `app/backend/`, `app/frontend/`, `scripts/prepdocs.py`, `infra/`, `.github/`. | Azure Developer CLI/infra-as-code; good sample discipline. | Citation rendering + thought-process panel + behavior settings. | Azure-specific services nếu bạn muốn cloud-neutral. | 5/5 |
| **infiniflow/ragflow** | ~82.2k★, Apache-2.0; RAG engine with Agent capabilities, enterprise-scale workflow. ([GitHub][39]) | `api/`, `web/`, `docker/`, `helm/`, `rag/`, document parsing modules. | Docker/K8s style. | Document QA product with sources, datasets, parsing pipeline. | Monolith lớn; đừng copy wholesale. | 5/5 |
| **langgenius/dify** | Open-source LLM app platform; workflow canvas, RAG, agents, model mgmt, observability; Docker Compose quickstart. ([GitHub][40]) | `api/`, `web/`, `docker/`, workflow canvas components. | `docker compose up -d`, env-based config. | Visual workflow builder, app/prompt/model abstraction. | No-code layer có thể che mất engineering portfolio nếu copy. | 5/4 |
| **open-webui/open-webui** | Self-hosted offline AI platform; RAG engine, Docker/K8s, granular permissions/user groups. ([GitHub][41]) | `backend/open_webui/`, frontend, routers, migrations, Docker. | Docker tags, CUDA/Ollama variants. | Auth/RBAC, knowledge base, chat UX, admin panels. | Không deploy public bản cũ/dev tag; security surface lớn. | 5/4 |
| **zylon-ai/private-gpt** | Apache-2.0; API layer for private AI apps, ingestion, citations, tools, MCP; workbench UI but API is product. ([GitHub][42]) | `private_gpt/`, server/API, settings, tests, `/ui`. | Configurable inference backend. | API-first backend primitives for document AI. | Không nhầm nó là model server; nó cần OpenAI-compatible backend. | 4/5 |
| **khoj-ai/khoj** | Self-hostable personal AI; docs/PDF/Markdown/Notion search, agents, automations. ([GitHub][43]) | `src/khoj/`, server, web/mobile integrations, docker-compose. | Self-host docs with DB. | Personal knowledge + agents + scheduled research. | License/architecture cần kiểm tra nếu reuse code. | 4/3 |
| **FlowiseAI/Flowise** | ~53.4k★, Apache-2.0, latest Apr 2026; visual agent builder. ([GitHub][44]) | Node editor, component registry, marketplace, Docker/deploy docs. | Many deploy targets. | Visual graph/node UI ideas. | Có reported critical RCE issue in older versions; không expose publicly without hardening. ([TechRadar][45]) | 4/3 |
| **deepset-ai/haystack-rag-app** | Example FastAPI + Haystack 2 + React UI + OpenSearch + OpenAI. ([GitHub][46]) | Backend FastAPI, React UI, OpenSearch wiring. | Docker-compose style sample. | Minimal full-stack RAG skeleton. | Toy-ish; dùng làm starter, không làm reference chính. | 3/4 |

---

## 8. Security / safety cho document AI

**Primary:** LLM Guard + Presidio + OWASP threat model.
**Red-team:** PyRIT/Garak/Promptfoo.
**Guardrail runtime:** NeMo Guardrails hoặc Guardrails AI.

| Repo | Threat model / license / activity | Guardrail implementation nên học | File/folder inspect | Tests/adversarial examples | Không nên copy | P/R |
|---|---|---|---|---|---|
| **protectai/llm-guard** | MIT; prompt injection, harmful language, data leakage, sanitization; designed for production integration. ([GitHub][47]) | Input/output scanners before and after LLM. | `llm_guard/input_scanners/`, `output_scanners/`, API docs. | Prompt injection + PII + sensitive output scanner tests. | Không coi scanner là absolute security boundary. | 4/5 |
| **microsoft/presidio** | PII detection/redaction/anonymization for text/images/structured data; docs warn automated detection is not guaranteed complete. ([GitHub][48]) | PII analyzer/anonymizer/image redactor. | `presidio-analyzer/`, `presidio-anonymizer/`, `presidio-image-redactor/`, samples. | Custom recognizers for legal IDs, names, addresses. | Không log raw PII before redaction. | 5/5 |
| **NVIDIA-NeMo/Guardrails** | Programmable rails for input/output/dialog/tool use; includes RAG fact-checking/eval tooling. ([GitHub][49]) | Rails config layer around LLM calls. | `nemoguardrails/`, `examples/`, `eval/`, `.co` rail configs. | Jailbreak, prompt injection, hallucination/fact-check eval. | DSL can become complex; avoid if simple validators enough. | 4/4 |
| **guardrails-ai/guardrails** | Input/Output Guards + structured output validation + validators hub. ([GitHub][50]) | Validators around LLM I/O. | `guardrails/`, hub validators, examples. | Schema validation, regex, PII validators. | Guardrails ≠ legal correctness verifier. | 3/4 |
| **microsoft/PyRIT** | MIT; open-source framework for proactive AI risk identification; v0.14.0 Jun 5 2026. ([GitHub][51]) | Red-team orchestration. | `pyrit/`, orchestrators, scorers, converters, memory. | Attack datasets, automated red-team runs. | Red-team outputs need triage; don’t auto-block from one score. | 4/4 |
| **NVIDIA/garak** | LLM vulnerability scanner; probes hallucination, data leakage, prompt injection, misinformation, toxicity, jailbreaks. ([GitHub][52]) | Scanner-style AI security testing. | `garak/probes/`, `generators/`, `detectors/`, reports. | Pre-release scan suite. | Model-level scan không cover full app tool permissions. | 4/3 |
| **promptfoo/promptfoo** | MIT; eval + red teaming + CI/CD. ([GitHub][23]) | CI red-team config. | `examples/redteam/`, providers, assertions. | Prompt injection, jailbreak, data exfiltration regression tests. | Đừng test only prompt; test uploaded-doc injection too. | 4/4 |
| **OWASP GenAI / LLM Top 10** | Threat model, not code; covers prompt injection, insecure output handling, supply chain, sensitive disclosure, excessive agency. ([OWASP Foundation][53]) | Security checklist for architecture. | LLM01, LLM02, LLM05, LLM06, LLM07, LLM08, LLM09. | Turn each risk into test cases. | Không treat as implementation; it is a taxonomy. | 3/5 |

---

# Prioritized shortlist

## 10 repo nên học trước

1. **RAGFlow** — học end-to-end document RAG product, citations, parsing, UI.
2. **Azure Search OpenAI Demo** — học FastAPI/React RAG UX, citation panel, infra.
3. **Docling** — học document object model + parsing pipeline.
4. **OCRmyPDF** — học robust OCR job pipeline.
5. **Vespa sample-apps** — học hybrid search/ranking/RAG blueprint.
6. **LangGraph** — học graph/state/human-in-loop orchestration.
7. **DeepEval** — học eval-as-tests.
8. **Langfuse** — học trace/prompt/eval dataset observability.
9. **Label Studio** — học human review / annotation queue.
10. **Presidio** — học PII redaction/anonymization cho legal docs.

## 5 libraries/frameworks nên cân nhắc dùng thật

1. **Docling** cho parsing canonical document.
2. **Qdrant** cho vector DB + metadata filtering.
3. **LangGraph** cho case workflow graph.
4. **DeepEval** cho CI regression eval.
5. **Langfuse** cho traces/prompt/eval datasets.

Fallback đáng cân nhắc: Unstructured, RAGAS, Phoenix, LLM Guard, Presidio.

## 5 architecture patterns quan trọng nhất

1. **Canonical Document Model:** `document_id -> page -> block -> span -> bbox -> source_uri -> checksum`.
2. **Hybrid Legal Retrieval:** BM25 + dense vector + metadata filter + reranker + citation verifier.
3. **Graph-based Case Workflow:** `case_intake -> ingest -> retrieve -> draft -> verify -> human_review -> final`.
4. **Trace-to-Eval Loop:** mọi failed trace được convert thành eval dataset/regression test.
5. **Human Review Audit Trail:** reviewer, decision, timestamp, evidence spans, model version, prompt version.

## 5 traps cần tránh

1. Upload PDF vào vector DB mà không lưu page/span/provenance.
2. Tin OCR/parser tuyệt đối, không có confidence/error handling.
3. Multi-agent role-play quá nhiều thay vì state machine rõ ràng.
4. Chỉ dùng LLM-as-judge mà không có gold cases/human calibration.
5. Expose file parser/agent tool/low-code workflow public mà không sandbox, RBAC, rate limit, audit log.

[1]: https://github.com/docling-project/docling "GitHub - docling-project/docling: Get your documents ready for gen AI · GitHub"
[2]: https://github.com/Unstructured-IO/unstructured "GitHub - Unstructured-IO/unstructured: Convert documents to structured data effortlessly. Unstructured is open-source ETL solution for transforming complex documents into clean, structured formats for language models.  Visit our website to learn more about our enterprise grade Platform product for production grade workflows, partitioning, enrichments, chunking and embedding. · GitHub"
[3]: https://github.com/ocrmypdf/ocrmypdf "GitHub - ocrmypdf/OCRmyPDF: OCRmyPDF adds an OCR text layer to scanned PDF files, allowing them to be searched · GitHub"
[4]: https://github.com/PaddlePaddle/PaddleOCR "GitHub - PaddlePaddle/PaddleOCR: Turn any PDF or image document into structured data for your AI. A powerful, lightweight OCR toolkit that bridges the gap between images/PDFs and LLMs. Supports 100+ languages. · GitHub"
[5]: https://github.com/datalab-to/marker "GitHub - datalab-to/marker: Convert PDF to markdown + JSON quickly with high accuracy · GitHub"
[6]: https://github.com/VikParuchuri/surya/blob/master/README.md "surya/README.md at master · datalab-to/surya · GitHub"
[7]: https://github.com/vespa-engine/sample-apps "GitHub - vespa-engine/sample-apps: Repository of sample applications for https://vespa.ai, the open big data serving engine · GitHub"
[8]: https://github.com/deepset-ai/haystack?utm_source=chatgpt.com "deepset-ai/haystack: Open-source AI orchestration ..."
[9]: https://github.com/qdrant/qdrant?utm_source=chatgpt.com "GitHub - qdrant/qdrant: Qdrant - High-performance ..."
[10]: https://github.com/run-llama/llama_index "GitHub - run-llama/llama_index: LlamaIndex is the leading document agent and OCR platform · GitHub"
[11]: https://github.com/langchain-ai/langchain "GitHub - langchain-ai/langchain: The agent engineering platform. · GitHub"
[12]: https://github.com/flagopen/flagembedding?utm_source=chatgpt.com "BGE: One-Stop Retrieval Toolkit For Search and RAG"
[13]: https://github.com/beir-cellar/beir?utm_source=chatgpt.com "beir-cellar/beir: A Heterogeneous Benchmark for ..."
[14]: https://github.com/langchain-ai/langgraph "GitHub - langchain-ai/langgraph: Build resilient agents. · GitHub"
[15]: https://github.com/pydantic/pydantic-ai?utm_source=chatgpt.com "AI Agent Framework, the Pydantic way"
[16]: https://github.com/openai/openai-agents-python?utm_source=chatgpt.com "OpenAI Agents SDK PyPI"
[17]: https://github.com/temporalio/samples-python?utm_source=chatgpt.com "Samples for working with the Temporal Python SDK"
[18]: https://github.com/microsoft/semantic-kernel "GitHub - microsoft/semantic-kernel: Integrate cutting-edge LLM technology quickly and easily into your apps · GitHub"
[19]: https://github.com/crewaiinc/crewai "GitHub - crewAIInc/crewAI: Framework for orchestrating role-playing, autonomous AI agents. By fostering collaborative intelligence, CrewAI empowers agents to work together seamlessly, tackling complex tasks. · GitHub"
[20]: https://github.com/microsoft/autogen "GitHub - microsoft/autogen: A programming framework for agentic AI · GitHub"
[21]: https://github.com/confident-ai/deepeval "GitHub - confident-ai/deepeval: The LLM Evaluation Framework · GitHub"
[22]: https://github.com/vibrantlabsai/ragas "GitHub - vibrantlabsai/ragas: Supercharge Your LLM Application Evaluations  · GitHub"
[23]: https://github.com/promptfoo/promptfoo?utm_source=chatgpt.com "Promptfoo: LLM evals & red teaming"
[24]: https://github.com/arize-ai/phoenix "GitHub - Arize-ai/phoenix: AI Observability & Evaluation · GitHub"
[25]: https://github.com/truera/trulens "GitHub - truera/trulens: Evaluation and Tracking for LLM Experiments and AI Agents · GitHub"
[26]: https://github.com/openai/evals "GitHub - openai/evals: Evals is a framework for evaluating LLMs and LLM systems, and an open-source registry of benchmarks. · GitHub"
[27]: https://github.com/UKGovernmentBEIS/inspect_ai?utm_source=chatgpt.com "UKGovernmentBEIS/inspect_ai: Inspect: A framework for ..."
[28]: https://github.com/evidentlyai/evidently?utm_source=chatgpt.com "evidentlyai/evidently: Evidently is ​​an open- ..."
[29]: https://github.com/langfuse/langfuse "GitHub - langfuse/langfuse:  Open source LLM engineering platform: LLM Observability, metrics, evals, prompt management, playground, datasets. Integrates with OpenTelemetry, Langchain, OpenAI SDK, LiteLLM, and more. YC W23 · GitHub"
[30]: https://github.com/helicone/helicone "GitHub - Helicone/helicone:  Open source LLM observability platform. One line of code to monitor, evaluate, and experiment. YC W23  · GitHub"
[31]: https://github.com/traceloop/openllmetry?utm_source=chatgpt.com "traceloop/openllmetry: Open-source observability for your ..."
[32]: https://github.com/open-telemetry/opentelemetry-python?utm_source=chatgpt.com "open-telemetry/opentelemetry-python"
[33]: https://github.com/mlflow/mlflow?utm_source=chatgpt.com "mlflow/mlflow: The open source AI engineering platform ..."
[34]: https://github.com/HumanSignal/label-studio "GitHub - HumanSignal/label-studio: Label Studio is a multi-type data labeling and annotation tool with standardized output format · GitHub"
[35]: https://github.com/argilla-io/argilla/ "GitHub - argilla-io/argilla: Argilla is a collaboration tool for AI engineers and domain experts to build high-quality datasets · GitHub"
[36]: https://github.com/doccano/doccano "GitHub - doccano/doccano: Open source annotation tool for machine learning practitioners. · GitHub"
[37]: https://github.com/orgs/HumanSignal/repositories "HumanSignal repositories · GitHub"
[38]: https://github.com/azure-samples/azure-search-openai-demo "GitHub - Azure-Samples/azure-search-openai-demo: A sample app for the Retrieval-Augmented Generation pattern running in Azure, using Azure AI Search for retrieval and Azure OpenAI large language models  to power ChatGPT-style and Q&A experiences. · GitHub"
[39]: https://github.com/infiniflow/ragflow "GitHub - infiniflow/ragflow: RAGFlow is a leading open-source Retrieval-Augmented Generation (RAG) engine that fuses cutting-edge RAG with Agent capabilities to create a superior context layer for LLMs · GitHub"
[40]: https://github.com/langgenius/dify "GitHub - langgenius/dify: Production-ready platform for agentic workflow development. · GitHub"
[41]: https://github.com/open-webui/open-webui "GitHub - open-webui/open-webui: User-friendly AI Interface (Supports Ollama, OpenAI API, ...) · GitHub"
[42]: https://github.com/zylon-ai/private-gpt "GitHub - zylon-ai/private-gpt: Interact with your documents using the power of GPT, 100% privately, no data leaks · GitHub"
[43]: https://github.com/khoj-ai/khoj "GitHub - khoj-ai/khoj: Your AI second brain. Self-hostable. Get answers from the web or your docs. Build custom agents, schedule automations, do deep research. Turn any online or local LLM into your personal, autonomous AI (gpt, claude, gemini, llama, qwen, mistral). Get started - free. · GitHub"
[44]: https://github.com/flowiseai/flowise "GitHub - FlowiseAI/Flowise: Build AI Agents, Visually · GitHub"
[45]: https://www.techradar.com/pro/security/top-open-source-ai-platform-flowise-hit-by-maximum-level-security-issue?utm_source=chatgpt.com "Top open source AI platform Flowise hit by maximum-level security issue"
[46]: https://github.com/deepset-ai/haystack-rag-app?utm_source=chatgpt.com "deepset-ai/haystack-rag-app: An example of a ..."
[47]: https://github.com/protectai/llm-guard "GitHub - protectai/llm-guard: The Security Toolkit for LLM Interactions · GitHub"
[48]: https://github.com/microsoft/presidio?utm_source=chatgpt.com "Presidio - Data Protection and De-identification SDK"
[49]: https://github.com/NVIDIA-NeMo/Guardrails "GitHub - NVIDIA-NeMo/Guardrails: NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems. · GitHub"
[50]: https://github.com/guardrails-ai/guardrails "GitHub - guardrails-ai/guardrails: Adding guardrails to large language models. · GitHub"
[51]: https://github.com/microsoft/PyRIT "GitHub - microsoft/PyRIT: The Python Risk Identification Tool for generative AI (PyRIT) is an open source framework built to empower security professionals and engineers to proactively identify risks in generative AI systems. · GitHub"
[52]: https://github.com/NVIDIA/garak "GitHub - NVIDIA/garak: the LLM vulnerability scanner · GitHub"
[53]: https://owasp.org/www-project-top-10-for-large-language-model-applications/ "OWASP Top 10 for Large Language Model Applications | OWASP Foundation"
