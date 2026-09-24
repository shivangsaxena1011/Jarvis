"""
SHIVANI Multi-Source Visual Grounding Engine (Phase 17).
Fuses evidence across Accessibility (UIA), DOM, Application APIs, OCR,
Vision detection, and Spatial relations to resolve UI elements with confidence.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from core.computer.models import ElementSource, ElementType, RectBounds, UIElement
from core.computer.semantic_graph import UISemanticGraph
from core.computer.spatial_engine import SpatialEngine


class GroundingResult(BaseModel):
    """Result of visual grounding analysis for an input target query."""
    element: Optional[UIElement] = None
    confidence: float = 0.0
    evidence_sources: List[ElementSource] = Field(default_factory=list)
    rationale: str = ""
    target_point: Optional[Tuple[int, int]] = None
    ambiguous: bool = False
    candidate_count: int = 0
    alternatives: List[UIElement] = Field(default_factory=list)


class MultiSourceGrounder:
    """Resolves natural language queries to high-confidence UI target elements."""

    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        self.spatial = SpatialEngine()

    def ground(
        self,
        query: str,
        elements: List[UIElement],
        semantic_graph: Optional[UISemanticGraph] = None,
        active_window_title: str = "",
    ) -> GroundingResult:
        """
        Grounds target query across elements using multi-source evidence.
        """
        q = query.strip()
        if not q or not elements:
            return GroundingResult(
                element=None,
                confidence=0.0,
                rationale="Empty query or no detected UI elements.",
                ambiguous=True,
            )

        # 1. Parse Spatial and Sectional Patterns
        # e.g., "button to the right of Search", "Save in Toolbar"
        spatial_match = self._match_spatial_query(q, elements)
        if spatial_match and spatial_match.confidence >= self.confidence_threshold:
            return spatial_match

        section_match = self._match_section_query(q, elements, semantic_graph)
        if section_match and section_match.confidence >= self.confidence_threshold:
            return section_match

        # 2. Candidate Search by Text & Type
        scored_candidates: List[Tuple[UIElement, float, List[ElementSource], str]] = []
        q_lower = q.lower()
        desired_type = self._extract_desired_type(q_lower)

        for elem in elements:
            score = 0.0
            sources = [elem.source]
            reasons = []

            elem_text = elem.text.strip().lower()

            # Exact text match
            if elem_text and elem_text == q_lower:
                score += 0.60
                reasons.append(f"Exact text match ('{elem.text}')")
            elif elem_text and (q_lower in elem_text or elem_text in q_lower):
                score += 0.40
                reasons.append(f"Partial text match ('{elem.text}')")

            # Element type boost
            if desired_type and elem.type == desired_type:
                score += 0.25
                reasons.append(f"Type match ({elem.type.value})")

            # Multi-source reinforcement boost
            if elem.source == ElementSource.ACCESSIBILITY:
                score += 0.15
            elif elem.source == ElementSource.DOM:
                score += 0.15
            elif elem.source == ElementSource.OCR:
                score += 0.10

            # State boost (visible + enabled)
            if elem.visible and elem.enabled:
                score += 0.05

            score = min(1.0, score)
            if score > 0.25:
                scored_candidates.append((elem, score, sources, "; ".join(reasons)))

        if not scored_candidates:
            return GroundingResult(
                element=None,
                confidence=0.0,
                rationale=f"No candidates found matching '{query}'.",
                ambiguous=True,
            )

        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_elem, top_score, top_sources, top_reason = scored_candidates[0]

        # Check for ambiguity: if runner-up has nearly identical score (>0.9 of top score)
        ambiguous = False
        alternatives = []
        if len(scored_candidates) > 1:
            runner_elem, runner_score, _, _ = scored_candidates[1]
            if abs(top_score - runner_score) < 0.08 and top_score < 0.90:
                ambiguous = True
                alternatives = [c[0] for c in scored_candidates[1:4]]

        return GroundingResult(
            element=top_elem,
            confidence=top_score,
            evidence_sources=top_sources,
            rationale=top_reason,
            target_point=top_elem.bounds.center,
            ambiguous=ambiguous or (top_score < self.confidence_threshold),
            candidate_count=len(scored_candidates),
            alternatives=alternatives,
        )

    def _extract_desired_type(self, q: str) -> Optional[ElementType]:
        if "button" in q:
            return ElementType.BUTTON
        if "input" in q or "field" in q or "textbox" in q:
            return ElementType.TEXT_FIELD
        if "tab" in q:
            return ElementType.TAB
        if "checkbox" in q:
            return ElementType.CHECKBOX
        if "radio" in q:
            return ElementType.RADIO
        if "link" in q:
            return ElementType.LINK
        if "menu" in q:
            return ElementType.MENU_ITEM
        return None

    def _match_spatial_query(self, query: str, elements: List[UIElement]) -> Optional[GroundingResult]:
        # Pattern: "<target> (left of|right of|above|below|near) <reference>"
        patterns = [
            r"(?P<rel>left of|right of|above|below|near|inside)\s+(?:the\s+)?(?P<ref>.+)",
            r"(?:the\s+)?(?P<target>.+)\s+(?P<rel>to the left of|to the right of|above|below|near)\s+(?:the\s+)?(?P<ref>.+)",
        ]

        for pat in patterns:
            m = re.search(pat, query, re.IGNORECASE)
            if m:
                rel = m.group("rel").lower().replace("to the ", "").replace(" ", "_")
                ref_text = m.group("ref").strip().lower()

                # Find reference element
                ref_elems = [e for e in elements if ref_text in e.text.lower()]
                if not ref_elems:
                    continue
                reference = ref_elems[0]

                # Filter candidates by relation
                filtered = self.spatial.filter_by_relation(elements, rel, reference)
                if filtered:
                    best = filtered[0]
                    return GroundingResult(
                        element=best,
                        confidence=0.88,
                        evidence_sources=[ElementSource.SPATIAL, best.source],
                        rationale=f"Resolved via spatial relation '{rel}' relative to '{reference.text}'",
                        target_point=best.bounds.center,
                        ambiguous=False,
                        candidate_count=len(filtered),
                    )
        return None

    def _match_section_query(
        self, query: str, elements: List[UIElement], semantic_graph: Optional[UISemanticGraph]
    ) -> Optional[GroundingResult]:
        # Pattern: "<control> in (the )?<section>" (e.g. "Save in toolbar")
        m = re.search(r"(?P<ctrl>.+)\s+in\s+(?:the\s+)?(?P<sec>toolbar|sidebar|statusbar|dialog|menu|header)", query, re.IGNORECASE)
        if m and semantic_graph:
            ctrl_text = m.group("ctrl").strip()
            sec_text = m.group("sec").strip()
            elem = semantic_graph.find_in_section(sec_text, ctrl_text)
            if elem:
                return GroundingResult(
                    element=elem,
                    confidence=0.92,
                    evidence_sources=[ElementSource.ACCESSIBILITY, ElementSource.SPATIAL],
                    rationale=f"Resolved '{ctrl_text}' inside section '{sec_text}' via semantic graph",
                    target_point=elem.bounds.center,
                    ambiguous=False,
                    candidate_count=1,
                )
        return None
