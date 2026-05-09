from __future__ import annotations

import os

import httpx

from packages.shared.python.ai_court_shared.env_config import load_repo_env
from packages.shared.python.ai_court_shared.schemas import (
    LegalSearchRequest,
    RemoteVectorSearchRequest,
    RemoteVectorSearchResponse,
)

load_repo_env()


class RemoteVectorClient:
    def __init__(self, base_url: str, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> "RemoteVectorClient | None":
        base_url = os.getenv("AI_COURT_VECTOR_API_URL", "").strip()
        if not base_url:
            return None
        timeout_seconds = float(os.getenv("AI_COURT_VECTOR_TIMEOUT_SECONDS", "30"))
        return cls(base_url=base_url, timeout_seconds=timeout_seconds)

    def search(self, request: LegalSearchRequest, top_k: int = 50) -> RemoteVectorSearchResponse:
        payload = RemoteVectorSearchRequest(
            query=request.query,
            top_k=top_k,
            filters=request.filters,
        )
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/search",
                json=payload.model_dump(mode="json"),
            )
            response.raise_for_status()
        return RemoteVectorSearchResponse.model_validate(response.json())
