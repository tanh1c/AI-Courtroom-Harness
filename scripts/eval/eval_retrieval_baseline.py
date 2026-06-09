from __future__ import annotations

import json
from pathlib import Path

from ai_court_retrieval.service import (
    get_local_legal_retrieval_service,
)
from ai_court_shared.schemas import LegalSearchRequest

QUERY_FILE = Path(__file__).with_name("retrieval_baseline_queries.json")
MIN_RECALL_AT_K = 0.80


def main() -> None:
    service = get_local_legal_retrieval_service()
    queries = json.loads(QUERY_FILE.read_text(encoding="utf-8"))

    total_expected = 0
    total_hits = 0

    for item in queries:
        request = LegalSearchRequest(query=item["query"], top_k=item.get("top_k", 3))
        response = service.search(request)
        returned_ids = [citation.citation_id for citation in response.citations]
        expected_ids = item["expected_citation_ids"]
        hits = len(set(returned_ids) & set(expected_ids))
        total_expected += len(expected_ids)
        total_hits += hits
        print(f"query={item['query']}")
        print(f"strategy={response.query_strategy}")
        print(f"returned={returned_ids}")
        print(f"expected={expected_ids}")
        print(f"hits={hits}/{len(expected_ids)}")
        print("---")

    recall_at_k = total_hits / total_expected if total_expected else 0.0
    print(f"recall_at_k={recall_at_k:.4f}")
    if recall_at_k < MIN_RECALL_AT_K:
        raise SystemExit(
            f"Retrieval baseline recall_at_k {recall_at_k:.4f} is below minimum {MIN_RECALL_AT_K:.2f}"
        )


if __name__ == "__main__":
    main()

