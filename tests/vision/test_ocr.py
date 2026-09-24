"""
Tests for OCR Subsystem (Extraction, Words, Lines, Fuzzy Matching, Multilingual).
"""

from PIL import Image, ImageDraw
from vision.ocr.engine import MockOCRBackend, create_default_ocr_engine
from vision.ocr.fuzzy import fuzzy_match_ratio, find_fuzzy_matches
from vision.ocr.multilingual import detect_script, normalize_multilingual_query
from vision.models.schemas import OCRWord, BoundingBox, CoordinateSpace


def test_fuzzy_matching_logic():
    assert fuzzy_match_ratio("submit", "submit") == 1.0
    assert fuzzy_match_ratio("submt", "submit") > 0.80
    assert fuzzy_match_ratio("search button", "search") >= 0.85
    assert fuzzy_match_ratio("completely_different", "search") < 0.40


def test_fuzzy_word_lookup():
    words = [
        OCRWord(text="Settings", bounding_box=BoundingBox(x=10, y=10, width=50, height=20)),
        OCRWord(text="Profile", bounding_box=BoundingBox(x=10, y=40, width=50, height=20)),
        OCRWord(text="Cancel", bounding_box=BoundingBox(x=10, y=70, width=50, height=20)),
    ]

    matches = find_fuzzy_matches(words, "Setings", threshold=0.7)
    assert len(matches) == 1
    assert matches[0][0].text == "Settings"
    assert matches[0][1] > 0.80


def test_multilingual_script_and_normalization():
    assert detect_script("Hello World") == "latin"
    assert detect_script("नमस्ते दुनिया") == "devanagari"

    # Hinglish query normalization
    assert normalize_multilingual_query("Chrome kholo") == "chrome open"
    assert normalize_multilingual_query("Settings band karo") == "settings close"
    assert normalize_multilingual_query("YouTube pe khojo") == "youtube pe search"


def test_mock_ocr_extraction():
    ocr = MockOCRBackend()
    # Create simple blank image
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    res = ocr.extract(img)

    assert len(res.words) >= 5
    assert len(res.lines) >= 1
    assert len(res.blocks) >= 1
    assert "Search" in res.full_text
    assert "Submit" in res.full_text

    # Search words
    found = res.find_text("Search")
    assert len(found) >= 1
    assert found[0].text == "Search"
