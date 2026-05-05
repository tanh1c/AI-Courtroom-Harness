from __future__ import annotations

from pydantic import BaseModel


class LegalChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    so_ky_hieu: str | None = None
    loai_van_ban: str | None = None
    ngay_ban_hanh: str | None = None
    ngay_co_hieu_luc: str | None = None
    ngay_het_hieu_luc: str | None = None
    tinh_trang_hieu_luc: str | None = None
    co_quan_ban_hanh: str | None = None
    linh_vuc: str | None = None
    article: str | None = None
    clause: str | None = None
    content: str
    source: str

