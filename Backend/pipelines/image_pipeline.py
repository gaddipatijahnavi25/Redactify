"""
Image pipeline: image/PDF → OCR → detect → visual redaction → PNG/PDF bytes.
"""
from __future__ import annotations

from pathlib import Path

from detection.detector import detect
from redaction.text_redactor import build_summary
from redaction.image_redactor import redact_image_file
from ocr.ocr_engine import extract_text


def process_image(path: Path) -> dict:
    """OCR + redact a single image file. Returns PNG bytes."""
    raw_text = extract_text(path)
    matches = detect(raw_text)
    pii_texts = {m.text for m in matches}

    redacted_bytes = redact_image_file(path, pii_texts)
    return {
        "out_bytes": redacted_bytes,
        "out_ext": ".png",
        "ocr_text": raw_text,
        "summary": build_summary(matches),
        "matches": [m.to_dict() for m in matches],
    }


def process_pdf(path: Path) -> dict:
    """
    Render each PDF page as an image, OCR → detect → redact,
    then re-combine into a single output PDF.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError("PyMuPDF not installed. Run: pip install PyMuPDF")

    all_matches = []
    all_ocr_text: list[str] = []
    page_images: list[bytes] = []

    doc = fitz.open(str(path))
    tmp_dir = path.parent

    for page_num, page in enumerate(doc):
        # Render page to image
        pix = page.get_pixmap(dpi=150)
        tmp_img = tmp_dir / f"_page_{page_num}_{path.stem}.png"
        pix.save(str(tmp_img))

        try:
            result = process_image(tmp_img)
            page_images.append(result["out_bytes"])
            all_matches.extend(result["matches"])
            all_ocr_text.append(result.get("ocr_text", ""))
        finally:
            tmp_img.unlink(missing_ok=True)

    doc.close()

    # Re-combine pages into a single PDF
    out_doc = fitz.open()
    for img_bytes in page_images:
        img_doc = fitz.open("png", img_bytes)
        rect = img_doc[0].rect
        out_page = out_doc.new_page(width=rect.width, height=rect.height)
        out_page.insert_image(rect, stream=img_bytes)
        img_doc.close()

    out_bytes = out_doc.tobytes()
    out_doc.close()

    # Rebuild PIIMatch objects for summary
    from detection.detector import PIIMatch
    match_objs = [
        PIIMatch(
            entity_type=m["entity_type"],
            text=m["text"],
            start=m["start"],
            end=m["end"],
            source=m.get("source", "regex"),
            score=m.get("score", 1.0),
        )
        for m in all_matches
    ]

    return {
        "out_bytes": out_bytes,
        "out_ext": ".pdf",
        "ocr_text": "\n\n".join(all_ocr_text),
        "summary": build_summary(match_objs),
        "matches": all_matches,
    }
