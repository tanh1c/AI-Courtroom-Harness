from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader
from packages.shared.python.ai_court_shared.schemas import (
    AttachmentParseResult,
    AttachmentParseStatus,
    CaseAttachment,
    CaseFileInput,
    CaseState,
    CaseStatus,
    CaseType,
    ClaimConfidence,
    Evidence,
    EvidenceStatus,
    EvidenceType,
    Fact,
    LegalIssue,
)

SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
WHITESPACE_PATTERN = re.compile(r"\s+")
ANCHOR_PATTERN = re.compile(r"\d{1,4}(?:[./]\d{1,4})+|\d[\d.,]*%?")
NARRATIVE_ONLY_HINTS = [
    "chua giao",
    "khong giao",
    "yeu cau",
    "boi thuong",
    "hoan tra",
    "chi phi phat sinh",
    "cho rang",
]
SUPPORT_KEYWORDS = [
    "hop dong",
    "giao xe",
    "giao hang",
    "giao tai san",
    "thanh toan",
    "chuyen khoan",
]


def normalize_text(text: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def fold_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    without_marks = "".join(character for character in normalized if not unicodedata.combining(character))
    return normalize_text(without_marks).lower()


def split_sentences(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    sentences = SENTENCE_SPLIT_PATTERN.split(normalized)
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def summarize_attachment(attachment: CaseAttachment) -> str:
    note = attachment.note or attachment.filename
    return f"Tệp `{attachment.filename}` được nộp làm chứng cứ với mô tả: {note}."


def classify_evidence_type(attachment: CaseAttachment) -> EvidenceType:
    haystack = " ".join(
        [
            attachment.filename.lower(),
            attachment.media_type.lower(),
            (attachment.note or "").lower(),
        ]
    )
    if "hợp đồng" in haystack or "contract" in haystack:
        return EvidenceType.CONTRACT
    if "biên lai" in haystack or "chuyển khoản" in haystack or "receipt" in haystack:
        return EvidenceType.PAYMENT_RECEIPT
    if "tin nhắn" in haystack or "message" in haystack or "chat" in haystack:
        return EvidenceType.MESSAGE
    return EvidenceType.OTHER


def truncate_text(text: str, limit: int = 320) -> str:
    normalized = normalize_text(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def extract_pdf_text(path: Path, max_pages: int = 3) -> str:
    reader = PdfReader(str(path))
    snippets: list[str] = []
    for page in reader.pages[:max_pages]:
        snippets.append(page.extract_text() or "")
    return normalize_text(" ".join(snippets))


def extract_text_attachment(path: Path, max_chars: int = 2000) -> str:
    return normalize_text(path.read_text(encoding="utf-8", errors="ignore")[:max_chars])


def build_attachment_parse_result(attachment: CaseAttachment) -> AttachmentParseResult:
    warnings: list[str] = []
    evidence_type = classify_evidence_type(attachment)
    source = f"attachment:{attachment.attachment_id}"
    local_path = attachment.local_path
    if not local_path:
        return AttachmentParseResult(
            attachment_id=attachment.attachment_id,
            filename=attachment.filename,
            media_type=attachment.media_type,
            note=attachment.note,
            local_path=local_path,
            detected_evidence_type=evidence_type,
            extraction_status=AttachmentParseStatus.METADATA_ONLY,
            source=source,
            warnings=warnings,
        )

    path = Path(local_path)
    if not path.exists():
        warnings.append("Local attachment path does not exist on disk.")
        return AttachmentParseResult(
            attachment_id=attachment.attachment_id,
            filename=attachment.filename,
            media_type=attachment.media_type,
            note=attachment.note,
            local_path=local_path,
            detected_evidence_type=evidence_type,
            extraction_status=AttachmentParseStatus.MISSING_FILE,
            source=source,
            warnings=warnings,
        )

    try:
        lowered_name = attachment.filename.lower()
        lowered_media_type = attachment.media_type.lower()
        extracted_text = ""
        if lowered_media_type == "application/pdf" or lowered_name.endswith(".pdf"):
            extracted_text = extract_pdf_text(path)
        elif lowered_media_type.startswith("text/") or lowered_name.endswith(".txt"):
            extracted_text = extract_text_attachment(path)
        else:
            warnings.append("Attachment type is not supported for local text extraction yet.")
            return AttachmentParseResult(
                attachment_id=attachment.attachment_id,
                filename=attachment.filename,
                media_type=attachment.media_type,
                note=attachment.note,
                local_path=local_path,
                detected_evidence_type=evidence_type,
                extraction_status=AttachmentParseStatus.METADATA_ONLY,
                source=source,
                warnings=warnings,
            )

        if not extracted_text:
            warnings.append("No readable text was extracted from the attachment.")
            return AttachmentParseResult(
                attachment_id=attachment.attachment_id,
                filename=attachment.filename,
                media_type=attachment.media_type,
                note=attachment.note,
                local_path=local_path,
                detected_evidence_type=evidence_type,
                extraction_status=AttachmentParseStatus.UNREADABLE,
                source=source,
                warnings=warnings,
            )

        return AttachmentParseResult(
            attachment_id=attachment.attachment_id,
            filename=attachment.filename,
            media_type=attachment.media_type,
            note=attachment.note,
            local_path=local_path,
            detected_evidence_type=evidence_type,
            extraction_status=AttachmentParseStatus.TEXT_EXTRACTED,
            extracted_text_excerpt=truncate_text(extracted_text),
            extracted_char_count=len(extracted_text),
            source=source,
            warnings=warnings,
        )
    except Exception as exc:
        warnings.append(f"Attachment text extraction failed: {exc}")
        return AttachmentParseResult(
            attachment_id=attachment.attachment_id,
            filename=attachment.filename,
            media_type=attachment.media_type,
            note=attachment.note,
            local_path=local_path,
            detected_evidence_type=evidence_type,
            extraction_status=AttachmentParseStatus.UNREADABLE,
            source=source,
            warnings=warnings,
        )


def build_attachment_parses(attachments: list[CaseAttachment]) -> list[AttachmentParseResult]:
    return [build_attachment_parse_result(attachment) for attachment in attachments]


def attachment_supports_sentence(
    sentence: str,
    attachment: CaseAttachment,
    parsed_attachment: AttachmentParseResult,
) -> bool:
    folded_sentence = fold_text(sentence)
    folded_attachment = fold_text(
        " ".join(
            [
                attachment.filename,
                attachment.note or "",
                parsed_attachment.extracted_text_excerpt or "",
            ]
        )
    )
    if not folded_attachment:
        return False

    for hint in NARRATIVE_ONLY_HINTS:
        if hint in folded_sentence and hint not in folded_attachment:
            return False

    shared_anchor_count = sum(
        1
        for anchor in set(ANCHOR_PATTERN.findall(folded_sentence))
        if anchor and anchor in folded_attachment
    )
    shared_keyword_count = sum(
        1
        for keyword in SUPPORT_KEYWORDS
        if keyword in folded_sentence and keyword in folded_attachment
    )

    if "hop dong" in folded_sentence and "hop dong" in folded_attachment:
        return shared_anchor_count >= 1 or shared_keyword_count >= 2

    return shared_anchor_count >= 2 or (shared_anchor_count >= 1 and shared_keyword_count >= 1)


def pick_fact_source(
    sentence: str,
    attachments: list[CaseAttachment],
    attachment_parses: list[AttachmentParseResult],
) -> str:
    for attachment, parsed_attachment in zip(attachments, attachment_parses):
        if attachment_supports_sentence(sentence, attachment, parsed_attachment):
            return f"attachment:{attachment.attachment_id}"
    return "narrative"


def infer_confidence(sentence: str, source: str) -> ClaimConfidence:
    lowered = sentence.lower()
    if source.startswith("attachment:"):
        return ClaimConfidence.HIGH
    if any(token in lowered for token in ["ngày", "đồng", "%"]):
        return ClaimConfidence.MEDIUM
    return ClaimConfidence.LOW


def build_facts(
    case_input: CaseFileInput,
    attachment_parses: list[AttachmentParseResult],
) -> list[Fact]:
    facts: list[Fact] = []
    for index, sentence in enumerate(split_sentences(case_input.narrative), start=1):
        source = pick_fact_source(sentence, case_input.attachments, attachment_parses)
        facts.append(
            Fact(
                fact_id=f"FACT_{index:03d}",
                content=sentence,
                source=source,
                confidence=infer_confidence(sentence, source),
            )
        )
    return facts


def build_attachment_facts(
    attachment_parses: list[AttachmentParseResult],
    start_index: int,
) -> list[Fact]:
    facts: list[Fact] = []
    next_index = start_index
    for attachment in attachment_parses:
        if not attachment.extracted_text_excerpt:
            continue
        facts.append(
            Fact(
                fact_id=f"FACT_{next_index:03d}",
                content=(
                    f"Nội dung trích xuất từ tệp {attachment.filename}: "
                    f"{attachment.extracted_text_excerpt}"
                ),
                source=attachment.source,
                confidence=ClaimConfidence.HIGH,
            )
        )
        next_index += 1
    return facts


def build_attachment_evidence(
    attachments: list[CaseAttachment],
    attachment_parses: list[AttachmentParseResult],
) -> list[Evidence]:
    evidence: list[Evidence] = []
    for index, (attachment, parsed_attachment) in enumerate(zip(attachments, attachment_parses), start=1):
        content = summarize_attachment(attachment)
        if parsed_attachment.extracted_text_excerpt:
            content = (
                f"{content} Trích đoạn đã đọc được: "
                f"{parsed_attachment.extracted_text_excerpt}"
            )
        evidence.append(
            Evidence(
                evidence_id=f"EVID_{index:03d}",
                type=parsed_attachment.detected_evidence_type,
                content=content,
                source=f"attachment:{attachment.attachment_id}",
                status=EvidenceStatus.UNCONTESTED,
            )
        )
    return evidence


def build_narrative_evidence(
    case_input: CaseFileInput,
    facts: list[Fact],
    start_index: int,
) -> list[Evidence]:
    evidence: list[Evidence] = []
    next_index = start_index
    for fact in facts:
        lowered = fact.content.lower()
        if any(keyword in lowered for keyword in ["tin nhắn", "trao đổi", "cho rằng", "yêu cầu"]):
            evidence.append(
                Evidence(
                    evidence_id=f"EVID_{next_index:03d}",
                    type=EvidenceType.MESSAGE,
                    content=f"Narrative statement captured for follow-up verification: {fact.content}",
                    source="narrative",
                    status=EvidenceStatus.DISPUTED,
                )
            )
            next_index += 1
    if (
        not evidence
        and any(
            keyword in case_input.narrative.lower()
            for keyword in ["không giao", "chậm giao", "không thực hiện", "chưa giao hàng", "chưa giao"]
        )
    ):
        evidence.append(
            Evidence(
                evidence_id=f"EVID_{next_index:03d}",
                type=EvidenceType.STATEMENT,
                content="Narrative alleges that one party did not perform the delivery obligation on time.",
                source="narrative",
                status=EvidenceStatus.DISPUTED,
            )
        )
    return evidence


def build_legal_issues(case_input: CaseFileInput, attachment_parses: list[AttachmentParseResult]) -> list[LegalIssue]:
    issues: list[LegalIssue] = []
    attachment_text = " ".join(
        attachment.extracted_text_excerpt or ""
        for attachment in attachment_parses
    ).lower()
    combined_text = f"{case_input.narrative.lower()} {attachment_text}"
    if any(
        keyword in combined_text
        for keyword in ["không giao", "chậm giao", "hạn giao", "giao xe", "giao hàng", "giao tài sản", "chưa giao"]
    ):
        issues.append(
            LegalIssue(
                issue_id=f"ISSUE_{len(issues) + 1:03d}",
                title="Nghĩa vụ giao tài sản theo hợp đồng",
                description="Xác định bên bán có vi phạm nghĩa vụ giao tài sản đúng thời hạn hay không.",
                tags=["contract", "delivery_obligation"],
            )
        )
    if any(keyword in combined_text for keyword in ["thanh toán", "chuyển khoản", "%", "trả trước"]):
        issues.append(
            LegalIssue(
                issue_id=f"ISSUE_{len(issues) + 1:03d}",
                title="Điều kiện và tiến độ thanh toán",
                description="Xác định nghĩa vụ thanh toán của bên mua theo thỏa thuận hợp đồng.",
                tags=["payment_terms", "contract_interpretation"],
            )
        )
    if any(keyword in combined_text for keyword in ["hoàn trả", "hoàn tiền", "bồi thường", "chi phí phát sinh"]):
        issues.append(
            LegalIssue(
                issue_id=f"ISSUE_{len(issues) + 1:03d}",
                title="Yêu cầu hoàn trả tiền và bồi thường",
                description="Xác định căn cứ cho yêu cầu hoàn trả khoản đã thanh toán và bồi thường thiệt hại.",
                tags=["refund", "damages"],
            )
        )
    if not issues:
        issues.append(
            LegalIssue(
                issue_id="ISSUE_001",
                title="Tranh chấp nghĩa vụ hợp đồng",
                description="Case needs manual review to refine the exact legal issues.",
                tags=["contract", "manual_review"],
            )
        )
    return issues


def parse_case_input(case_input: CaseFileInput) -> CaseState:
    attachment_parses = build_attachment_parses(case_input.attachments)
    narrative_facts = build_facts(case_input, attachment_parses)
    attachment_facts = build_attachment_facts(attachment_parses, len(narrative_facts) + 1)
    facts = narrative_facts + attachment_facts
    attachment_evidence = build_attachment_evidence(case_input.attachments, attachment_parses)
    narrative_evidence = build_narrative_evidence(case_input, narrative_facts, len(attachment_evidence) + 1)
    legal_issues = build_legal_issues(case_input, attachment_parses)

    return CaseState(
        case_id=case_input.case_id,
        title=case_input.title,
        case_type=CaseType(case_input.case_type),
        attachment_parses=attachment_parses,
        facts=facts,
        evidence=attachment_evidence + narrative_evidence,
        legal_issues=legal_issues,
        claims=[],
        citations=[],
        agent_turns=[],
        status=CaseStatus.PARSED,
    )
