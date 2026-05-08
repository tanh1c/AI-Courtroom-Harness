from __future__ import annotations

import re

from packages.shared.python.ai_court_shared.schemas import (
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


def normalize_text(text: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", text).strip()


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


def pick_fact_source(sentence: str, attachments: list[CaseAttachment]) -> str:
    lowered = sentence.lower()
    for attachment in attachments:
        note = (attachment.note or "").lower()
        filename = attachment.filename.lower()
        haystack = f"{note} {filename}"
        if "hợp đồng" in lowered and ("hợp đồng" in haystack or "contract" in haystack):
            return f"attachment:{attachment.attachment_id}"
        if (
            any(keyword in lowered for keyword in ["chuyển khoản", "thanh toán", "đặt cọc"])
            and any(keyword in haystack for keyword in ["biên", "receipt", "chuyển khoản"])
        ):
            return f"attachment:{attachment.attachment_id}"
        if (
            any(keyword in lowered for keyword in ["hạn giao", "giao xe", "giao hàng", "giao tài sản", "thỏa thuận"])
            and ("hợp đồng" in haystack or "contract" in haystack)
        ):
            return f"attachment:{attachment.attachment_id}"
    return "narrative"


def infer_confidence(sentence: str, source: str) -> ClaimConfidence:
    lowered = sentence.lower()
    if source.startswith("attachment:"):
        return ClaimConfidence.HIGH
    if any(token in lowered for token in ["ngày", "đồng", "%"]):
        return ClaimConfidence.MEDIUM
    return ClaimConfidence.LOW


def build_facts(case_input: CaseFileInput) -> list[Fact]:
    facts: list[Fact] = []
    for index, sentence in enumerate(split_sentences(case_input.narrative), start=1):
        source = pick_fact_source(sentence, case_input.attachments)
        facts.append(
            Fact(
                fact_id=f"FACT_{index:03d}",
                content=sentence,
                source=source,
                confidence=infer_confidence(sentence, source),
            )
        )
    return facts


def build_attachment_evidence(attachments: list[CaseAttachment]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for index, attachment in enumerate(attachments, start=1):
        evidence.append(
            Evidence(
                evidence_id=f"EVID_{index:03d}",
                type=classify_evidence_type(attachment),
                content=summarize_attachment(attachment),
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


def build_legal_issues(case_input: CaseFileInput) -> list[LegalIssue]:
    issues: list[LegalIssue] = []
    narrative = case_input.narrative.lower()
    if any(
        keyword in narrative
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
    if any(keyword in narrative for keyword in ["thanh toán", "chuyển khoản", "%", "trả trước"]):
        issues.append(
            LegalIssue(
                issue_id=f"ISSUE_{len(issues) + 1:03d}",
                title="Điều kiện và tiến độ thanh toán",
                description="Xác định nghĩa vụ thanh toán của bên mua theo thỏa thuận hợp đồng.",
                tags=["payment_terms", "contract_interpretation"],
            )
        )
    if any(keyword in narrative for keyword in ["hoàn trả", "hoàn tiền", "bồi thường", "chi phí phát sinh"]):
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
    facts = build_facts(case_input)
    attachment_evidence = build_attachment_evidence(case_input.attachments)
    narrative_evidence = build_narrative_evidence(case_input, facts, len(attachment_evidence) + 1)
    legal_issues = build_legal_issues(case_input)

    return CaseState(
        case_id=case_input.case_id,
        title=case_input.title,
        case_type=CaseType(case_input.case_type),
        facts=facts,
        evidence=attachment_evidence + narrative_evidence,
        legal_issues=legal_issues,
        claims=[],
        citations=[],
        agent_turns=[],
        status=CaseStatus.PARSED,
    )
