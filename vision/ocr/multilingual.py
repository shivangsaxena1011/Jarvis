"""
SHIVANI Multilingual OCR Helper (English, Hindi, Hinglish).
"""

import re
from typing import Optional


def detect_script(text: str) -> str:
    """Detects whether text is primarily Devanagari (Hindi) or Latin (English/Hinglish)."""
    devanagari_chars = sum(1 for ch in text if "\u0900" <= ch <= "\u097F")
    latin_chars = sum(1 for ch in text if ("a" <= ch.lower() <= "z"))

    if devanagari_chars > latin_chars:
        return "devanagari"
    return "latin"


# Common Hinglish terms mapped to English UI actions/labels
HINGLISH_TO_ENGLISH_MAP = {
    "kholo": "open",
    "band karo": "close",
    "khojo": "search",
    "bhejo": "send",
    "jama karo": "submit",
    "roko": "stop",
    "chalayein": "play",
    "dekho": "view",
    "hatao": "delete",
    "badlo": "edit",
    "likho": "type",
}


def normalize_multilingual_query(query: str) -> str:
    """Normalizes Hinglish voice/text queries to canonical UI terms when applicable."""
    q_clean = query.strip().lower()
    for hinglish, english in HINGLISH_TO_ENGLISH_MAP.items():
        if re.search(rf"\b{re.escape(hinglish)}\b", q_clean):
            return re.sub(rf"\b{re.escape(hinglish)}\b", english, q_clean)
    return q_clean
