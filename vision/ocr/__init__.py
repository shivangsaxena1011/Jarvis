"""
SHIVANI Vision OCR Subsystem.
"""

from vision.ocr.engine import (
    OCREngine,
    TesseractBackend,
    MockOCRBackend,
    create_default_ocr_engine,
)
from vision.ocr.fuzzy import (
    fuzzy_match_ratio,
    find_fuzzy_matches,
)
from vision.ocr.multilingual import (
    detect_script,
    normalize_multilingual_query,
)

__all__ = [
    "OCREngine",
    "TesseractBackend",
    "MockOCRBackend",
    "create_default_ocr_engine",
    "fuzzy_match_ratio",
    "find_fuzzy_matches",
    "detect_script",
    "normalize_multilingual_query",
]
