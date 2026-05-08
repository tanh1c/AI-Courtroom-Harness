# Colab Vector Setup

This guide runs the vector retrieval lane on Google Colab while the local app keeps BM25 search.

## 1. Local Preparation

From the repo root on your local machine:

```powershell
.\.venv\Scripts\python.exe scripts\ingest\build_legal_corpus.py --use-profile
```

This produces:

- `packages/retrieval/python/ai_court_retrieval/resources/mvp_legal_corpus.json`

Commit or push that file before moving to Colab so the notebook can clone the latest repo state.

## 2. Create an ngrok Token

1. Create an account at `https://ngrok.com/`.
2. Copy your auth token from the ngrok dashboard.

The Colab script uses ngrok to expose the vector API back to your local machine.

## 3. Open Colab and Run These Cells

### Cell 1: clone the repo

```python
!git clone https://github.com/tanh1c/AI-Courtroom-Harness.git
%cd AI-Courtroom-Harness
```

### Cell 2: install Colab-only dependencies

```python
!pip install -e . datasets sentence-transformers pyngrok
```

### Cell 3: start the vector server

Replace `YOUR_NGROK_TOKEN` before running:

```python
!python scripts/colab/start_vector_server.py --ngrok-token YOUR_NGROK_TOKEN
```

Wait until the output prints:

```text
PUBLIC_URL=https://...
```

Keep that Colab cell running.

## 4. Configure the Local App

In PowerShell on your local machine:

```powershell
$env:AI_COURT_VECTOR_API_URL="https://YOUR_PUBLIC_URL"
```

Then run the API:

```powershell
cd apps\api
..\..\.venv\Scripts\uvicorn.exe app.main:app --reload
```

## 5. Test Hybrid Search

From the repo root on your local machine:

```powershell
@'
from apps.api.app.main import legal_search
from packages.shared.python.ai_court_shared.schemas import LegalSearchRequest
response = legal_search(LegalSearchRequest(query="bên bán giao tài sản đúng thời hạn và bồi thường thiệt hại", top_k=5))
print(response.query_strategy)
for item in response.citations:
    print(item.article, item.title, item.retrieval_score)
'@ | .\.venv\Scripts\python.exe -
```

If the Colab server is reachable, `query_strategy` should be `hybrid`.

## 6. Expected Behavior

- If Colab is online, local retrieval uses `BM25 + remote vector fusion`.
- If Colab sleeps or the tunnel dies, the local app automatically falls back to `bm25_local`.

## 7. Restart Notes

- Re-run the Colab server cell when the runtime resets.
- Update `AI_COURT_VECTOR_API_URL` locally whenever ngrok gives a new public URL.
