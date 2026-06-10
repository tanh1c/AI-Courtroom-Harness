from __future__ import annotations

import math
from pathlib import Path

from pypdf import PdfReader

from ai_court_shared.schemas import (
    CaseAttachment,
    DocumentArtifact,
    DocumentArtifactKind,
    DocumentArtifactStatus,
)

CHUNK_SIZE = 1200
EXCERPT_SIZE = 500


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def classify_document_kind(attachment: CaseAttachment) -> DocumentArtifactKind:
    filename = attachment.filename.lower()
    media_type = attachment.media_type.lower()
    if media_type == "application/pdf" or filename.endswith(".pdf"):
        return DocumentArtifactKind.PDF
    if media_type.startswith("text/") or filename.endswith(".txt"):
        return DocumentArtifactKind.TEXT
    return DocumentArtifactKind.OTHER


def read_pdf_text(path: Path) -> tuple[str, int]:
    reader = PdfReader(str(path))
    snippets = [page.extract_text() or "" for page in reader.pages]
    return normalize_text(" ".join(snippets)), len(reader.pages)


def read_text_file(path: Path) -> str:
    return normalize_text(path.read_text(encoding="utf-8", errors="ignore"))


def build_document_artifact(index: int, attachment: CaseAttachment) -> DocumentArtifact:
    artifact_id = f"DOC_{index:03d}"
    source = f"attachment:{attachment.attachment_id}"
    kind = classify_document_kind(attachment)
    warnings: list[str] = []

    if not attachment.local_path:
        return DocumentArtifact(
            artifact_id=artifact_id,
            attachment_id=attachment.attachment_id,
            filename=attachment.filename,
            kind=kind,
            status=DocumentArtifactStatus.METADATA_ONLY,
            source=source,
            warnings=warnings,
        )

    path = Path(attachment.local_path)
    if not path.exists():
        warnings.append("Local attachment path does not exist on disk.")
        return DocumentArtifact(
            artifact_id=artifact_id,
            attachment_id=attachment.attachment_id,
            filename=attachment.filename,
            kind=kind,
            status=DocumentArtifactStatus.MISSING_FILE,
            source=source,
            warnings=warnings,
        )

    try:
        page_count = 0
        extracted_text = ""
        if kind == DocumentArtifactKind.PDF:
            extracted_text, page_count = read_pdf_text(path)
        elif kind == DocumentArtifactKind.TEXT:
            extracted_text = read_text_file(path)
            page_count = 1 if extracted_text else 0
        else:
            warnings.append("Attachment type is not supported for canonical text extraction yet.")
            return DocumentArtifact(
                artifact_id=artifact_id,
                attachment_id=attachment.attachment_id,
                filename=attachment.filename,
                kind=kind,
                status=DocumentArtifactStatus.METADATA_ONLY,
                source=source,
                warnings=warnings,
            )
    except Exception as exc:
        warnings.append(f"Document extraction failed: {exc}")
        return DocumentArtifact(
            artifact_id=artifact_id,
            attachment_id=attachment.attachment_id,
            filename=attachment.filename,
            kind=kind,
            status=DocumentArtifactStatus.UNREADABLE,
            source=source,
            warnings=warnings,
        )

    if not extracted_text:
        warnings.append("No readable text was extracted from the attachment.")
        return DocumentArtifact(
            artifact_id=artifact_id,
            attachment_id=attachment.attachment_id,
            filename=attachment.filename,
            kind=kind,
            status=DocumentArtifactStatus.UNREADABLE,
            page_count=page_count,
            source=source,
            warnings=warnings,
        )

    return DocumentArtifact(
        artifact_id=artifact_id,
        attachment_id=attachment.attachment_id,
        filename=attachment.filename,
        kind=kind,
        status=DocumentArtifactStatus.INGESTED,
        page_count=page_count,
        chunk_count=math.ceil(len(extracted_text) / CHUNK_SIZE),
        extracted_char_count=len(extracted_text),
        extracted_text_excerpt=extracted_text[:EXCERPT_SIZE],
        source=source,
        warnings=warnings,
    )


def build_document_artifacts(attachments: list[CaseAttachment]) -> list[DocumentArtifact]:
    return [build_document_artifact(index, attachment) for index, attachment in enumerate(attachments, start=1)]
