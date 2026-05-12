"""
Image redactor: draws filled black rectangles over PII word bounding boxes.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import cv2


def redact_image_file(image_path: Path, pii_texts: set[str]) -> bytes:
    """
    1. Read image with OpenCV.
    2. Use pytesseract to get word bounding boxes.
    3. Draw black rectangles over words whose text matches any PII token.
    4. Return PNG bytes.
    """
    import pytesseract

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Cannot open image: {image_path}")

    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    n = len(data["text"])

    pii_lower = {t.strip().lower() for t in pii_texts if t.strip()}

    for i in range(n):
        word = data["text"][i].strip()
        if not word:
            continue
        # Also match sub-tokens (e.g. phone broken across multiple OCR words)
        if word.lower() in pii_lower or _any_overlap(word.lower(), pii_lower):
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            pad = 3
            cv2.rectangle(img, (x - pad, y - pad), (x + w + pad, y + h + pad), (0, 0, 0), -1)

    _, encoded = cv2.imencode(".png", img)
    return encoded.tobytes()


def _any_overlap(word: str, pii_lower: set[str]) -> bool:
    """Check if word is a substring of any PII token or vice versa."""
    for pii in pii_lower:
        if len(word) >= 4 and (word in pii or pii in word):
            return True
    return False
