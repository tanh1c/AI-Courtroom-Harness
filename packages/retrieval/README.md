# Retrieval Package

This package contains the Phase 1 legal retrieval baseline.

Current contents:

- seed legal corpus resources
- HTML cleaning and article-aware chunking helpers
- local BM25 search with metadata filtering
- ingest script entrypoints for Hugging Face legal datasets

Next steps:

- build normalized chunks from the full legal corpus
- add vector retrieval with the legal embedding model
- merge lexical and vector candidates
- add reranking and retrieval evaluation
