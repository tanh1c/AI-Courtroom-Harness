from __future__ import annotations

import json
import logging
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
from .remote import RemoteVectorClient

ROOT_DIR = Path(__file__).resolve().parents[4]
DEFAULT_CORPUS_PATH = (
    ROOT_DIR
    / "packages"
    / "retrieval"
    / "python"
    / "ai_court_retrieval"
    / "resources"
    / "mvp_legal_corpus.json"
)
FALLBACK_CORPUS_PATH = (
    ROOT_DIR
    / "packages"
    / "retrieval"
    / "python"
    / "ai_court_retrieval"
    / "resources"
    / "seed_legal_corpus.json"
)
import re
TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
logger = logging.getLogger(__name__)


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
    def __init__(
        self,
        corpus_path: Path | None = None,
    ) -> None:
        default_corpus = DEFAULT_CORPUS_PATH if DEFAULT_CORPUS_PATH.exists() else FALLBACK_CORPUS_PATH
        self.corpus_path = corpus_path or default_corpus
        self.chunks = self._load_chunks()
        self.chunk_index_by_id = {chunk.chunk_id: index for index, chunk in enumerate(self.chunks)}
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

    def _bm25_rank(self, request: LegalSearchRequest) -> list[tuple[int, float]]:
        bm25_scores = self.bm25.get_scores(tokenize(request.query))
        ranked = [
            (index, float(score))
            for index, score in enumerate(bm25_scores)
            if self._matches_filters(self.chunks[index], request)
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked

    def _hybrid_rank(self, request: LegalSearchRequest) -> tuple[list[tuple[int, float]], RetrievalStrategy]:
        bm25_ranked = self._bm25_rank(request)
        remote_client = RemoteVectorClient.from_env()
        if remote_client is None:
            return bm25_ranked, RetrievalStrategy.BM25_LOCAL

        try:
            vector_response = remote_client.search(request, top_k=50)
        except Exception as exc:
            logger.warning("Remote vector search failed; falling back to BM25 only: %s", exc)
            return bm25_ranked, RetrievalStrategy.BM25_LOCAL

        fused_scores: dict[int, float] = {}
        for rank, (index, _) in enumerate(bm25_ranked[:50], start=1):
            fused_scores[index] = fused_scores.get(index, 0.0) + 1.0 / (60 + rank)
        for rank, result in enumerate(vector_response.results[:50], start=1):
            index = self.chunk_index_by_id.get(result.chunk_id)
            if index is None:
                continue
            fused_scores[index] = fused_scores.get(index, 0.0) + 1.0 / (60 + rank)

        return sorted(fused_scores.items(), key=lambda item: item[1], reverse=True), RetrievalStrategy.HYBRID

    def search(self, request: LegalSearchRequest) -> LegalSearchResponse:
        ranked, strategy = self._hybrid_rank(request)
        citations = [
            self._to_citation(self.chunks[index], score)
            for index, score in ranked[: request.top_k]
        ]
        return LegalSearchResponse(
            citations=citations,
            query_strategy=strategy,
        )


@lru_cache(maxsize=1)
def get_local_legal_retrieval_service() -> LocalLegalRetrievalService:
    return LocalLegalRetrievalService()
