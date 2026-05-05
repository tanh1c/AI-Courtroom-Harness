# Ingest Scripts

Place legal corpus ingestion scripts here.

Current entrypoint:

- `build_legal_corpus.py`: pulls metadata and content from Hugging Face, cleans HTML, applies article-aware chunking, and writes normalized chunks to `data/processed/`.

Note:

- Install the optional `datasets` package inside `.venv` before running this script.
