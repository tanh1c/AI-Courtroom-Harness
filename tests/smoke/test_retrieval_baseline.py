import json
from pathlib import Path

from ai_court_retrieval.service import get_local_legal_retrieval_service
from ai_court_shared.schemas import LegalSearchRequest, RetrievalStrategy

QUERY_FILE = Path(__file__).resolve().parents[2] / "scripts" / "eval" / "retrieval_baseline_queries.json"
MIN_RECALL_AT_K = 0.80


def test_retrieval_baseline_recall_threshold() -> None:
    service = get_local_legal_retrieval_service()
    queries = json.loads(QUERY_FILE.read_text(encoding="utf-8"))

    total_expected = 0
    total_hits = 0

    for item in queries:
        request = LegalSearchRequest(query=item["query"], top_k=item.get("top_k", 3))
        response = service.search(request)
        returned_ids = {citation.citation_id for citation in response.citations}
        expected_ids = set(item["expected_citation_ids"])

        assert response.query_strategy in {RetrievalStrategy.BM25_LOCAL, RetrievalStrategy.HYBRID}
        assert all(citation.doc_id and citation.chunk_id for citation in response.citations)
        assert all(citation.retrieval_method == response.query_strategy for citation in response.citations)

        total_expected += len(expected_ids)
        total_hits += len(returned_ids & expected_ids)

    recall_at_k = total_hits / total_expected
    assert recall_at_k >= MIN_RECALL_AT_K
