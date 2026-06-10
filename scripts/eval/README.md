# Evaluation Scripts

Place retrieval eval, harness negative tests, and smoke tests here.

Current entrypoints:

- `tests/smoke/test_imports.py`: verifies installed package-root imports through the repo-local `.venv`.
- `smoke_legal_search.py`: runs a local retrieval smoke check against the seed legal corpus.
- `eval_retrieval_baseline.py`: runs a tiny internal retrieval benchmark over seed-corpus queries and prints recall@k.
- `smoke_v1_hearing_runtime.py` and `smoke_v1_eval_cases.py`: validate V1 hearing runtime flows.
- `smoke_v2_trial_runtime.py` and `smoke_v2_eval_cases.py`: validate V2 trial runtime and report export flows.

Run smoke checks from the repository root with `.venv\Scripts\python.exe`; do not use the global Python interpreter.
