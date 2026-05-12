"""
Hybrid PII detector: regex patterns + spaCy NLP.
Falls back gracefully if spaCy model is not installed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

# ─── Regex patterns ────────────────────────────────────────────────────────────
_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL":       re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "PHONE_IN":    re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}"),
    "PHONE_INTL":  re.compile(r"\+?1?\s?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}"),
    "AADHAAR":     re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    "PAN":         re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "SSN":         re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "PASSPORT":    re.compile(r"\b[A-Z]{1,2}\d{6,7}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ \-]?){13,16}\b"),
    "IFSC":        re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    "IP_V4":       re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "DOB":         re.compile(
        r"\b(?:0?[1-9]|[12]\d|3[01])[/\-](?:0?[1-9]|1[0-2])[/\-](?:19|20)\d{2}\b"
    ),
    "URL":         re.compile(r"https?://[^\s]+"),
}

# ─── Optional spaCy ────────────────────────────────────────────────────────────
try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
    _NLP_AVAILABLE = True
except Exception:
    _nlp = None
    _NLP_AVAILABLE = False

# spaCy entity labels we want to capture
_NLP_LABELS = {"PERSON", "GPE", "LOC", "ORG", "DATE", "NORP"}


@dataclass
class PIIMatch:
    entity_type: str
    text: str
    start: int
    end: int
    source: str = "regex"       # "regex" | "nlp"
    score: float = 1.0

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "source": self.source,
            "score": round(self.score, 3),
        }


def _regex_matches(text: str) -> List[PIIMatch]:
    matches: List[PIIMatch] = []
    seen: set[tuple[int, int]] = set()
    for label, pattern in _PATTERNS.items():
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            if span not in seen:
                seen.add(span)
                matches.append(PIIMatch(
                    entity_type=label,
                    text=m.group(),
                    start=m.start(),
                    end=m.end(),
                    source="regex",
                    score=1.0,
                ))
    return matches


def _nlp_matches(text: str) -> List[PIIMatch]:
    if not _NLP_AVAILABLE or _nlp is None:
        return []
    doc = _nlp(text)
    return [
        PIIMatch(
            entity_type=ent.label_,
            text=ent.text,
            start=ent.start_char,
            end=ent.end_char,
            source="nlp",
            score=0.9,
        )
        for ent in doc.ents
        if ent.label_ in _NLP_LABELS
    ]


def _merge(regex: List[PIIMatch], nlp: List[PIIMatch]) -> List[PIIMatch]:
    """Merge regex + NLP results, removing overlapping spans (regex wins)."""
    all_hits = sorted(regex + nlp, key=lambda x: (x.start, -x.score))
    merged: List[PIIMatch] = []
    last_end = -1
    for hit in all_hits:
        if hit.start >= last_end:
            merged.append(hit)
            last_end = hit.end
    return merged


def detect(text: str) -> List[PIIMatch]:
    """Return merged PII matches from regex + spaCy."""
    return _merge(_regex_matches(text), _nlp_matches(text))
