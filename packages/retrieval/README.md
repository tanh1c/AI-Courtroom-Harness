# Retrieval Package

This package contains the Phase 1 legal retrieval baseline.

Current contents:

- real MVP legal corpus resources built from the Hugging Face dataset
- fallback seed corpus resources
- HTML cleaning and article-aware chunking helpers
- local BM25 search with metadata filtering
- local hashed-vector retrieval with reciprocal-rank hybrid fusion
- optional remote vector fusion support for Colab-hosted embeddings
- ingest script entrypoints for Hugging Face legal datasets

Next steps:

- expand beyond the curated MVP real-document profile
- replace hashed vectors with a persisted embedding index when model/runtime constraints allow it
- add reranking and broader retrieval evaluation
