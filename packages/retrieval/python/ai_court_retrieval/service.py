from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from rank_bm25 import BM25Okapi

from packages.shared.python.ai_court_shared.schemas import (
    Citation,
    EffectiveStatus,
    LegalSearchRequest,
    LegalSearchResponse,
    RetrievalStrategy,
)

from .models import LegalChunk

TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
ROOT_DIR = Path(__file__).resolve().parents[4]
SEED_CORPUS_PATH = (
    ROOT_DIR
    / "packages"
    / "retrieval"
    / "python"
    / "ai_court_retrieval"
    / "resources"
    / "seed_legal_corpus.json"
)


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def map_effective_status(value: str | None) -> EffectiveStatus:
    normalized = (value or "").strip().lower()
    if "còn hiệu lực" in normalized or normalized == "active":
        return EffectiveStatus.ACTIVE
    if "hết hiệu lực" in normalized or normalized == "expired":
        return EffectiveStatus.EXPIRED
    return EffectiveStatus.UNKNOWN


class LocalLegalRetrievalService:
    def __init__(self, corpus_path: Path | None = None) -> None:
        self.corpus_path = corpus_path or SEED_CORPUS_PATH
        self.chunks = self._load_chunks()
        self.tokenized_corpus = [tokenize(self._chunk_text(chunk)) for chunk in self.chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _load_chunks(self) -> list[LegalChunk]:
        payload = json.loads(self.corpus_path.read_text(encoding="utf-8"))
        return [LegalChunk.model_validate(item) for item in payload]

    def _chunk_text(self, chunk: LegalChunk) -> str:
        fields = [
            chunk.title,
            chunk.article or "",
            chunk.clause or "",
            chunk.content,
            chunk.loai_van_ban or "",
            chunk.linh_vuc or "",
        ]
        return " ".join(part for part in fields if part)

    def _matches_filters(self, chunk: LegalChunk, request: LegalSearchRequest) -> bool:
        filters = request.filters
        if filters.linh_vuc and (chunk.linh_vuc not in filters.linh_vuc):
            return False
        if filters.loai_van_ban and (chunk.loai_van_ban not in filters.loai_van_ban):
            return False
        if filters.co_quan_ban_hanh and (chunk.co_quan_ban_hanh not in filters.co_quan_ban_hanh):
            return False
        if filters.effective_status:
            status = map_effective_status(chunk.tinh_trang_hieu_luc)
            if status not in filters.effective_status:
                return False
        return True

    def _to_citation(self, chunk: LegalChunk, score: float) -> Citation:
        return Citation(
            citation_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            title=chunk.title,
            article=chunk.article or "",
            clause=chunk.clause,
            content=chunk.content,
            retrieval_score=round(score, 4),
            effective_status=map_effective_status(chunk.tinh_trang_hieu_luc),
            source=chunk.source,
        )

    def search(self, request: LegalSearchRequest) -> LegalSearchResponse:
        query_tokens = tokenize(request.query)
        scores = self.bm25.get_scores(query_tokens)
        ranked = sorted(
            (
                (index, float(score))
                for index, score in enumerate(scores)
                if self._matches_filters(self.chunks[index], request)
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        citations = [
            self._to_citation(self.chunks[index], score)
            for index, score in ranked[: request.top_k]
        ]
        return LegalSearchResponse(
            citations=citations,
            query_strategy=RetrievalStrategy.BM25_LOCAL_SEED,
        )


@lru_cache(maxsize=1)
def get_local_legal_retrieval_service() -> LocalLegalRetrievalService:
    return LocalLegalRetrievalService()

