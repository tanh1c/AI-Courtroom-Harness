from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from .models import LegalChunk

QUERY_PREFIX = (
    "Instruct: Given a Vietnamese legal question, retrieve relevant legal passages that answer the question\n"
    "Query: "
)


def chunk_to_passage(chunk: LegalChunk) -> str:
    parts = [
        chunk.title,
        chunk.article or "",
        chunk.clause or "",
        chunk.content,
    ]
    return "\n".join(part for part in parts if part)


def encode_query(model: SentenceTransformer, query: str) -> np.ndarray:
    embedding = model.encode(
        [f"{QUERY_PREFIX}{query}"],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(embedding, dtype=np.float32)


def build_vector_index(
    chunks: list[LegalChunk],
    model_name: str,
    output_embeddings_path: Path,
    output_metadata_path: Path,
) -> None:
    model = SentenceTransformer(model_name)
    passages = [chunk_to_passage(chunk) for chunk in chunks]
    embeddings = model.encode(
        passages,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=8,
    )
    np.save(output_embeddings_path, np.asarray(embeddings, dtype=np.float32))
    output_metadata_path.write_text(
        json.dumps(
            {
                "model_name": model_name,
                "chunk_ids": [chunk.chunk_id for chunk in chunks],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
