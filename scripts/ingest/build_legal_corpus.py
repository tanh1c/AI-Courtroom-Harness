from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.retrieval.python.ai_court_retrieval.ingest import (
    build_legal_chunks,
    build_legal_chunks_from_doc_ids,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a normalized legal corpus from Hugging Face datasets.")
    parser.add_argument("--dataset", default="th1nhng0/vietnamese-legal-documents")
    parser.add_argument("--metadata-config", default="metadata")
    parser.add_argument("--content-config", default="content")
    parser.add_argument("--split", default="data")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument(
        "--profile",
        default="packages/retrieval/python/ai_court_retrieval/resources/mvp_corpus_profile.json",
        help="JSON file with selected real document IDs for MVP retrieval.",
    )
    parser.add_argument(
        "--use-profile",
        action="store_true",
        help="Build the corpus from the repo's selected real document profile instead of generic dataset slicing.",
    )
    parser.add_argument(
        "--output",
        default="packages/retrieval/python/ai_court_retrieval/resources/mvp_legal_corpus.json",
        help="Output path for normalized chunk records.",
    )
    args = parser.parse_args()

    if args.use_profile:
        profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
        chunks = build_legal_chunks_from_doc_ids(profile["doc_ids"])
    else:
        try:
            from datasets import load_dataset
        except ImportError as exc:
            raise SystemExit(
                "Missing optional dependency 'datasets'. Install it in .venv before running this ingest script."
            ) from exc

        metadata = load_dataset(args.dataset, args.metadata_config, split=f"{args.split}[:{args.limit}]")
        content = load_dataset(args.dataset, args.content_config, split=f"{args.split}[:{args.limit}]")
        metadata_rows = [metadata[index] for index in range(len(metadata))]
        metadata_ids = {str(row["id"]) for row in metadata_rows}
        selected_content_rows = [row for row in content if str(row["id"]) in metadata_ids]
        chunks = build_legal_chunks(metadata_rows, selected_content_rows)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([chunk.model_dump() for chunk in chunks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(chunks)} chunks to {output_path}")


if __name__ == "__main__":
    main()
