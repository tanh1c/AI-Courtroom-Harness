from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.retrieval.python.ai_court_retrieval.service import (
    get_local_legal_retrieval_service,
)
from packages.shared.python.ai_court_shared.schemas import LegalSearchRequest


def main() -> None:
    service = get_local_legal_retrieval_service()
    request = LegalSearchRequest(
        query="giao xe dung han va boi thuong thiet hai do vi pham hop dong",
        top_k=3,
    )
    response = service.search(request)
    print(f"strategy={response.query_strategy}")
    for citation in response.citations:
        print(f"{citation.article} | {citation.title} | score={citation.retrieval_score}")


if __name__ == "__main__":
    main()
