"""
All regex patterns used by the PII detector.
Imported by detector.py – kept separate for easy extension.
"""
import re
from typing import Dict

PATTERNS: Dict[str, re.Pattern] = {
    # ── Contact ────────────────────────────────────────────────────────────────
    "EMAIL":        re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "PHONE_IN":     re.compile(r"(?:\+91[\s\-]?)?[6-9]\d{9}"),
    "PHONE_INTL":   re.compile(r"\+?1?\s?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}"),

    # ── Indian Government IDs ──────────────────────────────────────────────────
    "AADHAAR":      re.compile(r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    "PAN":          re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "VOTER_ID":     re.compile(r"\b[A-Z]{3}\d{7}\b"),
    "DRIVING_LIC":  re.compile(r"\b[A-Z]{2}\d{2}[\s\-]?\d{11}\b"),
    "VEHICLE_IN":   re.compile(r"\b[A-Z]{2}[\s\-]?\d{2}[\s\-]?[A-Z]{1,2}[\s\-]?\d{4}\b"),

    # ── International IDs ──────────────────────────────────────────────────────
    "SSN":          re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "PASSPORT":     re.compile(r"\b[A-Z]{1,2}\d{6,7}\b"),

    # ── Financial ─────────────────────────────────────────────────────────────
    "CREDIT_CARD":  re.compile(r"\b(?:\d[ \-]?){13,16}\b"),
    "IFSC":         re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    "UPI":          re.compile(r"[a-zA-Z0-9._\-]+@(?:okaxis|oksbi|okicici|okhdfcbank|paytm|ybl|upi)\b"),

    # ── Network ───────────────────────────────────────────────────────────────
    "IP_V4":        re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"),
    "MAC_ADDR":     re.compile(r"\b(?:[0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}\b"),
    "URL":          re.compile(r"https?://[^\s]+"),

    # ── Dates / Medical ───────────────────────────────────────────────────────
    "DOB":          re.compile(
        r"\b(?:0?[1-9]|[12]\d|3[01])[/\-](?:0?[1-9]|1[0-2])[/\-](?:19|20)\d{2}\b"
    ),
}
