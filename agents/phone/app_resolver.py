"""Natural Language Mobile Application Resolver.

Maps natural language requests (in English, Hindi, and Hinglish) to verified Android package names.
Handles fuzzy matching, aliases, and ambiguous app requests.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple


class AppResolver:
    """Resolves natural language app names to installed Android packages."""

    DEFAULT_APP_MAP: Dict[str, str] = {
        "instagram": "com.instagram.android",
        "linkedin": "com.linkedin.android",
        "settings": "com.android.settings",
        "setting": "com.android.settings",
        "photos": "com.google.android.apps.photos",
        "photo": "com.google.android.apps.photos",
        "gallery": "com.google.android.apps.photos",
        "youtube": "com.google.android.youtube",
        "chrome": "com.android.chrome",
        "browser": "com.android.chrome",
        "whatsapp": "com.whatsapp",
        "camera": "com.android.camera",
        "files": "com.google.android.apps.nbu.files",
        "file manager": "com.google.android.apps.nbu.files",
        "gmail": "com.google.android.gm",
        "mail": "com.google.android.gm",
        "maps": "com.google.android.apps.maps",
        "play store": "com.android.vending",
    }

    # Common Hindi / Hinglish filler patterns
    HINGLISH_PREFIXES = [
        r"^phone\s+(?:mein|pe|par|me|ko)\s+",
        r"^meri\s+",
        r"^apne\s+phone\s+(?:mein|pe|par|me)\s+",
    ]
    HINGLISH_SUFFIXES = [
        r"\s+(?:kholo|open\s+karo|launch\s+karo|chalao|start\s+karo|dekho)$",
        r"\s+(?:open|launch|start)$",
    ]

    def __init__(self, custom_app_map: Optional[Dict[str, str]] = None):
        self.app_map = dict(self.DEFAULT_APP_MAP)
        if custom_app_map:
            self.app_map.update(custom_app_map)

    def normalize_app_name(self, raw_input: str) -> str:
        """Strip conversational fillers and language suffixes to isolate the app name."""
        text = raw_input.strip().lower()

        # Strip prefixes
        for pattern in self.HINGLISH_PREFIXES:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Strip suffixes
        for pattern in self.HINGLISH_SUFFIXES:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Remove extra punctuation
        text = re.sub(r"[^\w\s-]", "", text).strip()
        return text

    def resolve_package(self, natural_query: str) -> Optional[str]:
        """Resolve a natural language query directly to a package name."""
        cleaned = self.normalize_app_name(natural_query)

        # Direct map lookup
        if cleaned in self.app_map:
            return self.app_map[cleaned]

        # Check if query already looks like a package identifier
        if "." in natural_query and natural_query.startswith("com."):
            return natural_query.strip()

        # Substring / fuzzy match
        best_match = None
        highest_ratio = 0.0

        for alias, pkg in self.app_map.items():
            if alias in cleaned or cleaned in alias:
                return pkg
            ratio = SequenceMatcher(None, cleaned, alias).ratio()
            if ratio > highest_ratio and ratio >= 0.70:
                highest_ratio = ratio
                best_match = pkg

        return best_match

    def find_candidates(self, natural_query: str) -> List[Tuple[str, str]]:
        """Return multiple possible candidates if query is ambiguous."""
        cleaned = self.normalize_app_name(natural_query)
        candidates = []

        for alias, pkg in self.app_map.items():
            ratio = SequenceMatcher(None, cleaned, alias).ratio()
            if ratio >= 0.55 or alias in cleaned or cleaned in alias:
                candidates.append((alias.title(), pkg))

        return candidates

    def register_installed_apps(self, package_dict: Dict[str, str]) -> None:
        """Dynamically add or update installed package mappings from device query."""
        for pkg, name in package_dict.items():
            self.app_map[name.lower()] = pkg
            self.app_map[pkg.lower()] = pkg
