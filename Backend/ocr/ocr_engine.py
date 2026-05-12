"""
OCR engine: wraps pytesseract for text extraction + word bounding boxes.
"""
from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image

from core.config import settings


def extract_text(image_path: Path) -> str:
    """Return full plain text from an image file."""
    img = Image.open(str(image_path)).convert("RGB")
    return pytesseract.image_to_string(img, lang=settings.ocr_language)


def extract_words(image_path: Path) -> list[dict]:
    """
    Return word-level data for bounding box redaction.
    Each item: {text, x, y, w, h, conf}
    """
    img = Image.open(str(image_path)).convert("RGB")
    data = pytesseract.image_to_data(
        img,
        lang=settings.ocr_language,
        output_type=pytesseract.Output.DICT,
    )
    words = []
    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        conf = int(data["conf"][i])
        if word and conf > 0:
            words.append({
                "text": word,
                "x": data["left"][i],
                "y": data["top"][i],
                "w": data["width"][i],
                "h": data["height"][i],
                "conf": conf,
            })
    return words
