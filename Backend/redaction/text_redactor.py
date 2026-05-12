"""
Text redactor: replace PII spans with [ENTITY_TYPE] labels.
Works character-level so it's accurate regardless of tokenisation.
"""
from __future__ import annotations

from typing import List
from detection.detector import PIIMatch


def redact_text(text: str, matches: List[PIIMatch]) -> str:
    """Replace all PII spans with labelled placeholders."""
    if not matches:
        return text

    # Sort spans and replace from end→start to keep offsets valid
    sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)
    chars = list(text)
    for m in sorted_matches:
        label = f"[{m.entity_type}]"
        chars[m.start:m.end] = list(label)
    return "".join(chars)


def build_summary(matches: List[PIIMatch]) -> dict:
    """Return aggregate counts by entity type."""
    from collections import Counter
    by_type = Counter(m.entity_type for m in matches)
    return {
        "total": len(matches),
        "by_type": dict(by_type),
        "nlp_count": sum(1 for m in matches if m.source == "nlp"),
        "regex_count": sum(1 for m in matches if m.source == "regex"),
    }
