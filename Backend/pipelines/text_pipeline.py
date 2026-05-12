"""
Text pipeline: TXT, CSV, JSON — with style/threshold/categories/scan_only support.
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd

from detection.detector import detect, PIIMatch
from redaction.text_redactor import build_summary


# ── core redact helper ────────────────────────────────────────────────────

def _redact(
    text: str,
    style: str = "label",
    threshold: float = 0.0,
    categories: Optional[List[str]] = None,
    scan_only: bool = False,
) -> tuple[str, list[PIIMatch]]:
    matches = detect(text)
    active = [
        m for m in matches
        if m.score >= threshold and (not categories or m.entity_type in categories)
    ]
    if scan_only:
        return text, active

    sorted_m = sorted(active, key=lambda m: m.start, reverse=True)
    chars = list(text)
    for m in sorted_m:
        original = text[m.start:m.end]
        if style == "stars":
            repl = "*" * len(original)
        elif style == "partial":
            repl = original[0] + "*" * max(0, len(original) - 2) + (original[-1] if len(original) > 1 else "")
        else:
            repl = f"[{m.entity_type}]"
        chars[m.start:m.end] = list(repl)

    return "".join(chars), active


# ── public pipeline functions ─────────────────────────────────────────────

def process_txt(path: Path, style="label", threshold=0.0, categories=None, scan_only=False) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    redacted, active = _redact(raw, style, threshold, categories, scan_only)
    return {
        "out_bytes": redacted.encode("utf-8"),
        "out_ext": ".txt",
        "original_text": raw,
        "redacted_text": redacted,
        "summary": build_summary(active),
        "matches": [m.to_dict() for m in active],
    }


def process_csv(path: Path, style="label", threshold=0.0, categories=None, scan_only=False) -> dict:
    df = pd.read_csv(path, dtype=str).fillna("")
    all_matches: list[PIIMatch] = []
    original_rows = df.to_csv(index=False)

    def _cell(val: str) -> str:
        if not isinstance(val, str) or not val.strip():
            return val
        redacted, m = _redact(val, style, threshold, categories, scan_only)
        all_matches.extend(m)
        return redacted

    df = df.map(_cell)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    redacted_text = buf.getvalue()
    return {
        "out_bytes": redacted_text.encode("utf-8"),
        "out_ext": ".csv",
        "original_text": original_rows,
        "redacted_text": redacted_text,
        "summary": build_summary(all_matches),
        "matches": [m.to_dict() for m in all_matches],
    }


def _redact_value(value: Any, style, threshold, categories, scan_only) -> tuple[Any, list[PIIMatch]]:
    all_m: list[PIIMatch] = []
    if isinstance(value, str):
        r, m = _redact(value, style, threshold, categories, scan_only)
        return r, m
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            out[k], m = _redact_value(v, style, threshold, categories, scan_only)
            all_m.extend(m)
        return out, all_m
    if isinstance(value, list):
        out_l = []
        for item in value:
            r, m = _redact_value(item, style, threshold, categories, scan_only)
            out_l.append(r); all_m.extend(m)
        return out_l, all_m
    return value, []


def process_json(path: Path, style="label", threshold=0.0, categories=None, scan_only=False) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    original_text = json.dumps(data, indent=2, ensure_ascii=False)
    redacted_data, all_matches = _redact_value(data, style, threshold, categories, scan_only)
    redacted_text = json.dumps(redacted_data, indent=2, ensure_ascii=False)
    return {
        "out_bytes": redacted_text.encode("utf-8"),
        "out_ext": ".json",
        "original_text": original_text,
        "redacted_text": redacted_text,
        "summary": build_summary(all_matches),
        "matches": [m.to_dict() for m in all_matches],
    }
