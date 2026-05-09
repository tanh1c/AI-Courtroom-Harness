# Current MVP Architecture

This file documents the current backend-first MVP architecture for `AI Courtroom Harness`.

Use the Mermaid source below as the canonical diagram source. You can render it into a PNG or SVG later and place the exported image at:

- `docs/architecture/assets/mvp-architecture.png`

```mermaid
flowchart TD
    U[User or Demo Script] --> API[FastAPI API Layer]

    subgraph Intake[Case Intake Plane]
        API --> CASES[Cases API]
        CASES --> ATTACH[Attachment Upload]
        ATTACH --> PARSER[Heuristic Parser and PDF Text Extraction]
        PARSER --> STATE[Case State Builder]
        STATE --> SQLITE[(SQLite Store)]
        STATE --> SNAP[(JSON Snapshots)]
    end

    subgraph Retrieval[Legal Retrieval Plane]
        STATE --> SEARCH[Legal Search Service]
        SEARCH --> BM25[BM25 Local Index]
        SEARCH --> VECTOR[Remote Vector Client]
        VECTOR --> COLAB[Colab Vector Service]
        BM25 --> CORPUS[MVP Legal Corpus]
        COLAB --> CORPUS
    end

    subgraph Runtime[Courtroom Runtime Plane]
        STATE --> GRAPH[LangGraph Courtroom Flow]
        SEARCH --> GRAPH
        GRAPH --> P[Plaintiff Agent]
        GRAPH --> D[Defense Agent]
        GRAPH --> J[Judge Agent]
        GRAPH --> C[Clerk Agent]
        P --> LLM[Provider Abstraction]
        D --> LLM
        J --> LLM
        C --> LLM
        LLM --> OR[OpenRouter Ring]
        LLM --> GQ[Groq Qwen]
        LLM --> NV[NVIDIA]
        LLM --> NR[9Router]
        LLM --> OL[Ollama Cloud]
        LLM --> HF[Heuristic Fallback]
    end

    subgraph Safety[Verification and Review Plane]
        GRAPH --> VERIFY[Verification Service]
        VERIFY --> CITE[Citation Verifier]
        VERIFY --> CLAIM[Unsupported Claim Detector]
        VERIFY --> CONTRA[Contradiction Checker]
        VERIFY --> AUDIT[Audit Trail]
        VERIFY --> REVIEW[Human Review Gate]
    end

    subgraph Output[Reporting Plane]
        REVIEW --> REPORT[Final Report Builder]
        REPORT --> MD[Markdown Export]
        REPORT --> HTML[HTML Preview]
        MD --> SNAP
        HTML --> SNAP
    end

    API --> GETS[Read Endpoints and Report Endpoints]
    GETS --> SQLITE
    GETS --> SNAP
```

## Read It As A Harness

The important architectural idea is that this repo is not a single prompt-response chatbot.

Instead, it is a staged legal harness with:

- persisted case state
- structured retrieval
- role-constrained agent generation
- post-generation verification
- human review before final export
