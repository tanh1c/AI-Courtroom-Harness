from __future__ import annotations

import re
from pathlib import Path

from ai_court_shared.schemas import (
    ClaimConfidence,
    SecurityGuardrailFinding,
    SecurityGuardrailResponse,
)

MAX_NARRATIVE_CHARS = 12_000
MAX_SEARCH_QUERY_CHARS = 800
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
ALLOWED_MEDIA_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/octet-stream",
}
ALLOWED_SUFFIXES = {".pdf", ".txt", ".md"}
PROMPT_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"system\s*prompt",
        r"developer\s*message",
        r"reveal\s+(your\s+)?(prompt|instructions|secrets)",
        r"bypass\s+(the\s+)?(guardrails|safety|policy)",
    ]
]


def _finding(index: int, field: str, message: str, severity: ClaimConfidence = ClaimConfidence.HIGH) -> SecurityGuardrailFinding:
    return SecurityGuardrailFinding(
        finding_id=f"SECURITY_{index:03d}",
        field=field,
        severity=severity,
        message=message,
    )


def _text_findings(field: str, value: str, max_chars: int) -> list[SecurityGuardrailFinding]:
    findings: list[SecurityGuardrailFinding] = []
    if len(value) > max_chars:
        findings.append(_finding(len(findings) + 1, field, f"{field} exceeds {max_chars} characters."))
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(value):
            findings.append(_finding(len(findings) + 1, field, "Prompt-injection instruction detected at API boundary."))
            break
    return findings


def validate_case_payload(title: str, narrative: str) -> SecurityGuardrailResponse:
    findings = _text_findings("title", title, 240) + _text_findings("narrative", narrative, MAX_NARRATIVE_CHARS)
    renumbered = [
        SecurityGuardrailFinding(
            finding_id=f"SECURITY_{index:03d}",
            field=finding.field,
            severity=finding.severity,
            message=finding.message,
        )
        for index, finding in enumerate(findings, start=1)
    ]
    return SecurityGuardrailResponse(allowed=not renumbered, findings=renumbered)


def validate_search_query(query: str) -> SecurityGuardrailResponse:
    findings = _text_findings("query", query, MAX_SEARCH_QUERY_CHARS)
    return SecurityGuardrailResponse(allowed=not findings, findings=findings)


def validate_attachment(filename: str, media_type: str, size_bytes: int) -> SecurityGuardrailResponse:
    findings: list[SecurityGuardrailFinding] = []
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        findings.append(_finding(len(findings) + 1, "file", f"Attachment type {suffix or '<none>'} is not allowed."))
    if media_type not in ALLOWED_MEDIA_TYPES:
        findings.append(_finding(len(findings) + 1, "media_type", f"Media type {media_type} is not allowed."))
    if size_bytes > MAX_ATTACHMENT_BYTES:
        findings.append(_finding(len(findings) + 1, "file", f"Attachment exceeds {MAX_ATTACHMENT_BYTES} bytes."))
    return SecurityGuardrailResponse(allowed=not findings, findings=findings)
