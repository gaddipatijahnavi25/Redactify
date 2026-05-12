"""
Report generator: produce a structured JSON audit report.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List


def generate_report(
    *,
    filename: str,
    file_type: str,
    summary: dict,
    matches: List[dict],
    confidence_estimate: float | None = None,
) -> dict:
    """
    Build a structured report dict to be included in the API response.
    """
    total = summary.get("total", len(matches))
    confidence = confidence_estimate if confidence_estimate is not None else (
        0.95 if summary.get("regex_count", 0) > 0 else 0.80
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filename": filename,
        "file_type": file_type,
        "pii_summary": {
            "total_detected": total,
            "by_category": summary.get("by_type", {}),
            "regex_detections": summary.get("regex_count", 0),
            "nlp_detections": summary.get("nlp_count", 0),
            "confidence_estimate": round(confidence, 3),
        },
        "detections": [
            {
                "entity_type": m.get("entity_type"),
                "original_text": m.get("text"),
                "source": m.get("source", "regex"),
                "score": m.get("score", 1.0),
            }
            for m in matches
        ],
    }
