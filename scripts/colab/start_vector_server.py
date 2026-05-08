from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path

import numpy as np
import uvicorn
from fastapi import FastAPI

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.retrieval.python.ai_court_retrieval.models import LegalChunk
from packages.shared.python.ai_court_shared.schemas import (
    RemoteVectorSearchRequest,
    RemoteVectorSearchResponse,
    RemoteVectorSearchResult,
)


def load_chunks(corpus_path: Path) -> list[LegalChunk]:
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    return [LegalChunk.model_validate(item) for item in payload]


def load_vector_metadata(metadata_path: Path) -> dict:
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def create_app(
    corpus_path: Path,
    embeddings_path: Path,
    metadata_path: Path,
) -> FastAPI:
    from packages.retrieval.python.ai_court_retrieval.vector import encode_query
    from sentence_transformers import SentenceTransformer

    chunks = load_chunks(corpus_path)
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    embeddings = np.load(embeddings_path)
    metadata = load_vector_metadata(metadata_path)
    model = SentenceTransformer(metadata["model_name"])

    app = FastAPI(title="AI Court Vector Search", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/search", response_model=RemoteVectorSearchResponse)
    def search(request: RemoteVectorSearchRequest) -> RemoteVectorSearchResponse:
        query_embedding = encode_query(model, request.query)[0]
        cosine_scores = embeddings @ query_embedding
        ranked = sorted(
            (
                RemoteVectorSearchResult(chunk_id=chunk_ids[index], score=float(score))
                for index, score in enumerate(cosine_scores)
                if _matches_filters(chunks[index], request.filters)
            ),
            key=lambda item: item.score,
            reverse=True,
        )
        return RemoteVectorSearchResponse(
            results=ranked[: request.top_k],
            model_name=metadata["model_name"],
        )

    return app


def _matches_filters(chunk: LegalChunk, filters) -> bool:
    if filters.linh_vuc and (chunk.linh_vuc not in filters.linh_vuc):
        return False
    if filters.loai_van_ban and (chunk.loai_van_ban not in filters.loai_van_ban):
        return False
    if filters.co_quan_ban_hanh and (chunk.co_quan_ban_hanh not in filters.co_quan_ban_hanh):
        return False
    if filters.effective_status:
        status_text = (chunk.tinh_trang_hieu_luc or "").lower()
        allowed = {status.value for status in filters.effective_status}
        if "còn hiệu lực" in status_text:
            normalized = "active"
        elif "hết hiệu lực" in status_text:
            normalized = "expired"
        else:
            normalized = "unknown"
        if normalized not in allowed:
            return False
    return True


def ensure_vector_index(
    corpus_path: Path,
    embeddings_path: Path,
    metadata_path: Path,
    model_name: str,
) -> None:
    from packages.retrieval.python.ai_court_retrieval.vector import build_vector_index

    if embeddings_path.exists() and metadata_path.exists():
        return
    chunks = load_chunks(corpus_path)
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    build_vector_index(chunks, model_name, embeddings_path, metadata_path)


def run_server(app: FastAPI, host: str, port: int) -> None:
    uvicorn.run(app, host=host, port=port, log_level="info")


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Colab vector search server for AI Court.")
    parser.add_argument(
        "--corpus-path",
        default=str(ROOT_DIR / "packages" / "retrieval" / "python" / "ai_court_retrieval" / "resources" / "mvp_legal_corpus.json"),
    )
    parser.add_argument(
        "--embeddings-path",
        default="/content/data/indexes/mvp_legal_corpus_embeddings.npy",
    )
    parser.add_argument(
        "--metadata-path",
        default="/content/data/indexes/mvp_legal_corpus_embeddings.meta.json",
    )
    parser.add_argument(
        "--model-name",
        default="mainguyen9/vietlegal-harrier-0.6b",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--ngrok-token", required=True)
    args = parser.parse_args()

    from pyngrok import ngrok

    corpus_path = Path(args.corpus_path)
    embeddings_path = Path(args.embeddings_path)
    metadata_path = Path(args.metadata_path)

    ensure_vector_index(corpus_path, embeddings_path, metadata_path, args.model_name)
    app = create_app(corpus_path, embeddings_path, metadata_path)

    ngrok.set_auth_token(args.ngrok_token)
    tunnel = ngrok.connect(addr=args.port, bind_tls=True)
    print(f"PUBLIC_URL={tunnel.public_url}")

    thread = threading.Thread(target=run_server, args=(app, args.host, args.port), daemon=True)
    thread.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        ngrok.disconnect(tunnel.public_url)
        ngrok.kill()


if __name__ == "__main__":
    main()
