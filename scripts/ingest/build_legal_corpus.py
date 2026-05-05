from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.retrieval.python.ai_court_retrieval.ingest import build_legal_chunks


def main() -> None:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit(
            "Missing optional dependency 'datasets'. Install it in .venv before running this ingest script."
        ) from exc

    parser = argparse.ArgumentParser(description="Build a normalized legal corpus from Hugging Face datasets.")
    parser.add_argument("--dataset", default="th1nhng0/vietnamese-legal-documents")
    parser.add_argument("--metadata-config", default="metadata")
    parser.add_argument("--content-config", default="content")
    parser.add_argument("--split", default="train")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument(
        "--output",
        default="data/processed/legal_corpus_sample.json",
        help="Output path for normalized chunk records.",
    )
    args = parser.parse_args()

    metadata = load_dataset(args.dataset, args.metadata_config, split=args.split)
    content = load_dataset(args.dataset, args.content_config, split=args.split)

    metadata_rows = [metadata[index] for index in range(min(args.limit, len(metadata)))]
    metadata_ids = {str(row["id"]) for row in metadata_rows}

    selected_content_rows = []
    for row in content:
        if str(row["id"]) in metadata_ids:
            selected_content_rows.append(row)
        if len(selected_content_rows) >= len(metadata_rows):
            break

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
