"""
Extended API router with all endpoints:
  POST /api/redact        – file upload redaction (+ style/threshold/categories)
  POST /api/redact-text   – raw text redaction
  POST /api/scan          – detect-only (no redaction), returns highlighted spans
"""
from __future__ import annotations

import base64
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.config import settings
from core.file_type import detect_file_type, FileType
from detection.detector import detect, PIIMatch
from redaction.text_redactor import build_summary
from reporting.report import generate_report
from pipelines.text_pipeline import process_txt, process_csv, process_json
from pipelines.image_pipeline import process_image, process_pdf

router = APIRouter()


# ── Redaction style helpers ───────────────────────────────────────────────

def _apply_style(text: str, matches: List[PIIMatch], style: str, threshold: float, categories: Optional[List[str]]) -> str:
    """Apply redaction with chosen style, threshold, and category filter."""
    if not matches:
        return text

    active = [
        m for m in sorted(matches, key=lambda x: x.start, reverse=True)
        if m.score >= threshold and (not categories or m.entity_type in categories)
    ]

    chars = list(text)
    for m in active:
        original = text[m.start:m.end]
        if style == "stars":
            replacement = "*" * len(original)
        elif style == "partial":
            # Keep first char + *** + last char for longer strings
            if len(original) > 3:
                replacement = original[0] + "*" * (len(original) - 2) + original[-1]
            else:
                replacement = "*" * len(original)
        else:  # label (default)
            replacement = f"[{m.entity_type}]"
        chars[m.start:m.end] = list(replacement)

    return "".join(chars)


def _save_upload(file: UploadFile) -> Path:
    uid = uuid.uuid4().hex[:8]
    dest = settings.upload_dir / f"{uid}_{file.filename}"
    with dest.open("wb") as f:
        f.write(file.file.read())
    return dest


def _save_output(out_bytes: bytes, original_name: str, out_ext: str) -> Path:
    stem = Path(original_name).stem
    dest = settings.output_dir / f"redacted_{stem}{out_ext}"
    dest.write_bytes(out_bytes)
    return dest


# ── POST /api/redact ──────────────────────────────────────────────────────

@router.post("/redact")
async def redact_file(
    file: UploadFile = File(...),
    style: str = Form("label"),          # label | stars | partial
    threshold: float = Form(0.0),        # 0.0–1.0 min confidence
    categories: str = Form(""),          # comma-sep list, empty = all
    scan_only: bool = Form(False),       # detect without redacting
):
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(400, detail=f"Unsupported file type '{ext}'.")

    cat_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else []
    upload_path = _save_upload(file)
    file_type = detect_file_type(file.filename)

    try:
        if file_type == FileType.TEXT:
            result = process_txt(upload_path, style=style, threshold=threshold, categories=cat_list, scan_only=scan_only)
        elif file_type == FileType.CSV:
            result = process_csv(upload_path, style=style, threshold=threshold, categories=cat_list, scan_only=scan_only)
        elif file_type == FileType.JSON:
            result = process_json(upload_path, style=style, threshold=threshold, categories=cat_list, scan_only=scan_only)
        elif file_type == FileType.IMAGE:
            result = process_image(upload_path)
        elif file_type == FileType.PDF:
            result = process_pdf(upload_path)
        else:
            raise HTTPException(422, detail="Cannot process this file type.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, detail=str(exc)) from exc

    out_path = _save_output(result["out_bytes"], file.filename, result["out_ext"])
    report = generate_report(
        filename=file.filename, file_type=file_type.value,
        summary=result["summary"], matches=result["matches"],
    )

    response = {
        "filename": file.filename,
        "file_type": file_type.value,
        "scan_only": scan_only,
        "redacted_filename": out_path.name,
        "redacted_file_b64": base64.b64encode(result["out_bytes"]).decode(),
        "report": report,
    }
    # Include original + redacted text for diff view (text types only)
    if "original_text" in result:
        response["original_text"] = result["original_text"]
        response["redacted_text"] = result["redacted_text"]

    return JSONResponse(response)


# ── POST /api/redact-text ─────────────────────────────────────────────────

class TextRequest(BaseModel):
    text: str
    style: str = "label"
    threshold: float = 0.0
    categories: List[str] = []
    scan_only: bool = False


@router.post("/redact-text")
async def redact_text_endpoint(req: TextRequest):
    if not req.text.strip():
        raise HTTPException(400, detail="Text is empty.")

    matches = detect(req.text)
    active = [
        m for m in matches
        if m.score >= req.threshold and (not req.categories or m.entity_type in req.categories)
    ]

    if req.scan_only:
        redacted = req.text
    else:
        redacted = _apply_style(req.text, matches, req.style, req.threshold, req.categories or None)

    summary = build_summary(active)
    report = generate_report(
        filename="<text input>", file_type="text",
        summary=summary, matches=[m.to_dict() for m in active],
    )

    return JSONResponse({
        "original_text": req.text,
        "redacted_text": redacted,
        "file_type": "text",
        "scan_only": req.scan_only,
        "report": report,
        "spans": [m.to_dict() for m in active],  # for highlight rendering
    })


# ── POST /api/scan ────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    text: str
    threshold: float = 0.0
    categories: List[str] = []


@router.post("/scan")
async def scan_text(req: ScanRequest):
    """Detect-only: return PII spans without redacting."""
    if not req.text.strip():
        raise HTTPException(400, detail="Text is empty.")

    matches = detect(req.text)
    active = [
        m for m in matches
        if m.score >= req.threshold and (not req.categories or m.entity_type in req.categories)
    ]

    return JSONResponse({
        "spans": [m.to_dict() for m in active],
        "summary": build_summary(active),
        "total": len(active),
    })
