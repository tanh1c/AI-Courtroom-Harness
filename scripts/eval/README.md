# Evaluation Scripts

Place retrieval eval, harness negative tests, and smoke tests here.

Current entrypoint:

- `smoke_legal_search.py`: runs a local retrieval smoke check against the seed legal corpus.
- `eval_retrieval_baseline.py`: runs a tiny internal retrieval benchmark over seed-corpus queries and prints recall@k.
