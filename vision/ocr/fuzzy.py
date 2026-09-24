"""
SHIVANI OCR Fuzzy Matching and Query Resolution.
"""

from typing import List, Tuple
import difflib
from vision.models.schemas import OCRWord


def fuzzy_match_ratio(str1: str, str2: str) -> float:
    """Calculates normalized similarity ratio in [0.0, 1.0]."""
    s1 = str1.strip().lower()
    s2 = str2.strip().lower()
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    if s1 in s2 or s2 in s1:
        # Boost substring matches
        return max(0.85, difflib.SequenceMatcher(None, s1, s2).ratio())
    return difflib.SequenceMatcher(None, s1, s2).ratio()


def find_fuzzy_matches(
    words: List[OCRWord],
    query: str,
    threshold: float = 0.7,
) -> List[Tuple[OCRWord, float]]:
    """
    Finds OCR words matching query with similarity >= threshold.
    Returns list of (OCRWord, similarity_score) sorted descending by score.
    """
    matches: List[Tuple[OCRWord, float]] = []
    q_clean = query.strip().lower()

    for word in words:
        score = fuzzy_match_ratio(q_clean, word.text)
        if score >= threshold:
            matches.append((word, score))

    matches.sort(key=lambda item: item[1], reverse=True)
    return matches
