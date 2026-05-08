# Ingest Scripts

Place legal corpus ingestion scripts here.

Current entrypoint:

- `build_legal_corpus.py`: builds normalized chunks either from the curated MVP real-document profile or from generic dataset slices.
- `build_vector_index.py`: encodes the MVP real corpus with the legal embedding model and writes vector artifacts to `data/indexes/`.
- `../colab/start_vector_server.py`: preferred way to build embeddings and serve vector search remotely from Colab.

Note:

- Install the optional `datasets` package inside `.venv` for generic dataset slicing.
- The vector index builder requires `sentence-transformers` and a compatible Python environment.
