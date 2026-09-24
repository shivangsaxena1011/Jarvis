"""
SHIVANI Context & Hinglish Normalizer
Maintains conversational and environmental context (active window, current file, last target).
Normalizes Hindi/Hinglish instructions into canonical intent representations.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# Common Hindi / Hinglish vocabulary mappings
HINGLISH_ACTION_MAP = [
    # Summarize & Extract (Browser Intelligence)
    (r"\b(?:is webpage ka summary batao|is page ka summary batao|summary batao|summary do|summarize karo|summary nikalo)\b", "summarize this page"),
    (r"\b(?:ye webpage se important information extract karo|is webpage se data extract karo|information extract karo|extract karo)\b", "extract information from webpage"),
    (r"\b(?:is webpage ka|is page ka|ye webpage ka|ye page ka)\b", "this webpage"),
    (r"\b(?:ye webpage se|is webpage se|is page se)\b", "from this webpage"),
    # Search on engine / site (e.g., "Google pe ... search karo")
    (r"\bpe\s+(.*?)\s+search karo\b", r"search \1 on"),
    (r"\bka song search karo\b", "search song"),
    (r"\bka gana search karo\b", "search song"),
    # Play / Media (specific first)
    (r"\b(?:ye song play karo|is song ko play karo|gana chalao|gana chala do|gana bajao|play karo)\b", "play song"),
    (r"\bgana\b", "song"),
    # Minimize / Maximize / Restore / Switch (Window Management)
    (r"\b(?:ko minimize karo|minimize karo|chhota karo)\b", "minimize"),
    (r"\b(?:ko maximize karo|maximize karo|bada karo)\b", "maximize"),
    (r"\b(?:ko restore karo|restore karo)\b", "restore"),
    (r"\b(?:pe wapas jao|par wapas jao|pe jao|par jao|pe switch karo)\b", "switch to"),
    # Screenshot / Vision
    (r"\b(?:screenshot lo|screenshot le lo|screen capture karo|photo lo)\b", "take screenshot"),
    # Open / Launch
    (r"\b(?:kholo|khol|chalao|chala do|start karo|shuru karo|launch karo)\b", "open"),
    # Close / Exit
    (r"\b(?:band karo|hata do|close karo|exit karo)\b", "close"),
    # Check / Inspect / Search / Find
    (r"\b(?:check karo|dekho|dhoondo|dhundo|search karo|talaash karo|find karo)\b", "search and check"),
    # Clean / Delete
    (r"\b(?:clean karo|saaf karo|delete karo|mita do)\b", "clean and delete"),
    # Create / Write / Type
    (r"\b(?:type karo)\b", "type"),
    (r"\b(?:banao|likho|post karo|ready karo|draft karo)\b", "create and draft"),
]

# Deictic referent patterns (pointing to current context)
DEICTIC_PATTERNS = [
    r"\bye\s+wala\b",
    r"\bisko\b",
    r"\busko\b",
    r"\bise\b",
    r"\buse\b",
    r"\bthis\s+one\b",
]


class SessionContext(BaseModel):
    current_app: Optional[str] = None
    current_window: Optional[str] = None
    current_file: Optional[str] = None
    last_target: Optional[str] = None
    recent_history: List[str] = Field(default_factory=list)

    def update_environment(self, app: Optional[str] = None, window: Optional[str] = None, file_path: Optional[str] = None, target: Optional[str] = None) -> None:
        if app:
            self.current_app = app
        if window:
            self.current_window = window
        if file_path:
            self.current_file = file_path
        if target:
            self.last_target = target


class HinglishNormalizer:
    @staticmethod
    def strip_wake_word(text: str, wake_word: str = "Shivani") -> str:
        pattern = rf"^\s*{wake_word}[,\s]*"
        return re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    @staticmethod
    def normalize(text: str, context: Optional[SessionContext] = None) -> str:
        """
        Normalizes Hindi/Hinglish speech to semantic intent while maintaining context.
        """
        cleaned = text.strip()
        
        # Resolve deictic referents ("ye wala", "isko") using context if available
        if context:
            referent = context.current_file or context.last_target or context.current_window
            if referent:
                for pat in DEICTIC_PATTERNS:
                    cleaned = re.sub(pat, f"'{referent}'", cleaned, flags=re.IGNORECASE)

        # Apply action mappings
        normalized = cleaned
        for pattern, replacement in HINGLISH_ACTION_MAP:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        return normalized.strip()
