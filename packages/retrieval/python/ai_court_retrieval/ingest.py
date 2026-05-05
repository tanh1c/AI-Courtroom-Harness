from __future__ import annotations

import re
from typing import Iterable

from bs4 import BeautifulSoup

from .models import LegalChunk

ARTICLE_PATTERN = re.compile(r"(?=Điều\s+\d+[A-Za-z0-9\-]*)", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_html_content(content_html: str) -> str:
    soup = BeautifulSoup(content_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def split_legal_articles(text: str) -> list[tuple[str | None, str]]:
    normalized = WHITESPACE_PATTERN.sub(" ", text).strip()
    if not normalized:
        return []

    parts = [part.strip() for part in ARTICLE_PATTERN.split(normalized) if part.strip()]
    if not parts:
        return [(None, normalized)]

    chunks: list[tuple[str | None, str]] = []
    for part in parts:
        match = re.match(r"(Điều\s+\d+[A-Za-z0-9\-]*)", part, flags=re.IGNORECASE)
        article = match.group(1) if match else None
        chunks.append((article, part))
    return chunks


def build_legal_chunks(
    metadata_rows: Iterable[dict],
    content_rows: Iterable[dict],
    source: str = "vbpl.vn",
) -> list[LegalChunk]:
    metadata_by_id = {str(row["id"]): row for row in metadata_rows}
    chunks: list[LegalChunk] = []

    for content_row in content_rows:
        doc_id = str(content_row["id"])
        metadata = metadata_by_id.get(doc_id)
        if not metadata:
            continue

        cleaned = clean_html_content(content_row.get("content_html", ""))
        article_splits = split_legal_articles(cleaned) or [(None, cleaned)]

        for index, (article, content) in enumerate(article_splits, start=1):
            chunks.append(
                LegalChunk(
                    chunk_id=f"LAW_CHUNK_{doc_id}_{index:03d}",
                    doc_id=doc_id,
                    title=str(metadata.get("title", "")),
                    so_ky_hieu=metadata.get("so_ky_hieu"),
                    loai_van_ban=metadata.get("loai_van_ban"),
                    ngay_ban_hanh=metadata.get("ngay_ban_hanh"),
                    ngay_co_hieu_luc=metadata.get("ngay_co_hieu_luc"),
                    ngay_het_hieu_luc=metadata.get("ngay_het_hieu_luc"),
                    tinh_trang_hieu_luc=metadata.get("tinh_trang_hieu_luc"),
                    co_quan_ban_hanh=metadata.get("co_quan_ban_hanh"),
                    linh_vuc=metadata.get("linh_vuc"),
                    article=article,
                    clause=None,
                    content=content,
                    source=source,
                )
            )

    return chunks

