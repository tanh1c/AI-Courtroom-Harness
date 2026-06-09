from apps.api.app.document_ingestion import build_document_artifacts
from ai_court_shared.schemas import CaseAttachment, DocumentArtifactStatus


def test_text_attachment_builds_canonical_document_artifact(tmp_path) -> None:
    source = tmp_path / "contract.txt"
    source.write_text("Contract signed on 2026-01-24. Payment remains disputed.", encoding="utf-8")

    artifacts = build_document_artifacts([
        CaseAttachment(
            attachment_id="ATT_001",
            filename="contract.txt",
            media_type="text/plain",
            local_path=str(source),
        )
    ])

    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.artifact_id == "DOC_001"
    assert artifact.attachment_id == "ATT_001"
    assert artifact.status == DocumentArtifactStatus.INGESTED
    assert artifact.page_count == 1
    assert artifact.chunk_count == 1
    assert artifact.extracted_char_count > 0
    assert artifact.source == "attachment:ATT_001"
    assert "Payment remains disputed" in (artifact.extracted_text_excerpt or "")
