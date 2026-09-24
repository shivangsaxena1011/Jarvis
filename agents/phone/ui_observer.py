"""Android UI Observer and Minimal Accessibility Tree Analyzer.

Enforces data minimization, locates interactive targets (buttons, inputs, messages),
and integrates semantic UI resolution with vision fallbacks.
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from core.bridge.models import UIElementNode, VisibleUIObservation

logger = logging.getLogger("shivani.phone.observer")


class AndroidUIObserver:
    """Interprets Android Accessibility trees and finds actionable UI nodes."""

    def find_target_element(
        self,
        query: str,
        observation: VisibleUIObservation,
        prefer_clickable: bool = True,
    ) -> Optional[UIElementNode]:
        """Locate a UI element matching query text, description, or resource id."""
        clean_query = query.strip().lower()
        candidates: List[tuple[float, UIElementNode]] = []

        all_nodes = self._flatten_elements(observation.elements)

        for node in all_nodes:
            # Check text
            score = 0.0
            node_text = (node.text or "").strip().lower()
            node_desc = (node.content_desc or "").strip().lower()
            node_id = (node.resource_id or "").strip().lower()

            if clean_query == node_text or clean_query == node_desc:
                score = 1.0
            elif clean_query in node_text or clean_query in node_desc:
                score = 0.85
            elif clean_query in node_id:
                score = 0.75
            else:
                ratio_text = SequenceMatcher(None, clean_query, node_text).ratio() if node_text else 0.0
                ratio_desc = SequenceMatcher(None, clean_query, node_desc).ratio() if node_desc else 0.0
                score = max(ratio_text, ratio_desc)

            if prefer_clickable and node.clickable:
                score += 0.15

            if score >= 0.60:
                candidates.append((score, node))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def extract_visible_text_summary(self, observation: VisibleUIObservation) -> List[str]:
        """Extract only visible textual content for summarization tasks (e.g. messages, posts).

        Enforces data minimization: ignores layout wrappers and empty nodes.
        """
        all_nodes = self._flatten_elements(observation.elements)
        lines = []
        for node in all_nodes:
            text = (node.text or "").strip()
            desc = (node.content_desc or "").strip()
            if text:
                lines.append(text)
            elif desc and desc not in ("Back", "Home", "Navigate up", "More options"):
                lines.append(desc)
        return lines

    def _flatten_elements(self, nodes: List[UIElementNode]) -> List[UIElementNode]:
        """Recursively flatten hierarchical node tree into single list."""
        flat = []
        for node in nodes:
            flat.append(node)
            if node.children:
                flat.extend(self._flatten_elements(node.children))
        return flat
