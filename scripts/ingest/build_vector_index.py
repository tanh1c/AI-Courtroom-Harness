from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.retrieval.python.ai_court_retrieval.models import LegalChunk
from packages.retrieval.python.ai_court_retrieval.vector import build_vector_index


def main() -> None:
    corpus_path = ROOT_DIR / "packages" / "retrieval" / "python" / "ai_court_retrieval" / "resources" / "mvp_legal_corpus.json"
    embeddings_path = ROOT_DIR / "data" / "indexes" / "mvp_legal_corpus_embeddings.npy"
    metadata_path = ROOT_DIR / "data" / "indexes" / "mvp_legal_corpus_embeddings.meta.json"
    model_name = "mainguyen9/vietlegal-harrier-0.6b"

    chunks = [
        LegalChunk.model_validate(item)
        for item in json.loads(corpus_path.read_text(encoding="utf-8"))
    ]
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    build_vector_index(chunks, model_name, embeddings_path, metadata_path)
    print(f"Wrote embeddings to {embeddings_path}")


if __name__ == "__main__":
    main()
