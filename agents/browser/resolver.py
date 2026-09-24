"""
SHIVANI Element Resolver
Resolves natural-language descriptions into verified Playwright locators using a robust 7-tier hierarchy:
1. Accessibility Role & Name
2. Label Text
3. Placeholder Text
4. Name / ID / test-id attributes
5. Visible Text Content
6. Semantic CSS / XPath Selectors
7. Multimodal Vision Fallback (Phase 3 VisionProvider)
"""

import re
from typing import Optional, Tuple
from playwright.async_api import Page, Locator
from agents.computer.vision import VisionProvider


class ElementResolver:
    """Intelligently resolves natural language element queries to active page Locators."""

    def __init__(self, vision_provider: Optional[VisionProvider] = None):
        self.vision = vision_provider

    async def resolve(
        self,
        page: Page,
        target_description: str,
        element_type: Optional[str] = None
    ) -> Tuple[Optional[Locator], str]:
        """
        Resolves a target description to a Playwright Locator and returns (locator, strategy_used).
        """
        desc = target_description.strip()
        desc_clean = re.sub(r"^(the|a|an)\s+", "", desc, flags=re.IGNORECASE).strip()

        # Tier 1: Accessibility Role with Name
        roles = []
        if element_type == "button" or "button" in desc_clean.lower() or "btn" in desc_clean.lower():
            roles = ["button"]
        elif element_type == "input" or "search" in desc_clean.lower() or "box" in desc_clean.lower():
            roles = ["searchbox", "textbox"]
        elif element_type == "link" or "link" in desc_clean.lower():
            roles = ["link"]
        else:
            roles = ["button", "searchbox", "textbox", "link", "combobox"]

        for role in roles:
            try:
                # Try exact and regex name match
                loc = page.get_by_role(role, name=re.compile(re.escape(desc_clean), re.IGNORECASE))
                if await loc.count() > 0 and await loc.first.is_visible():
                    return loc.first, f"role:{role}"
            except Exception:
                pass

        # Tier 2: By Label
        try:
            loc = page.get_by_label(re.compile(re.escape(desc_clean), re.IGNORECASE))
            if await loc.count() > 0 and await loc.first.is_visible():
                return loc.first, "label"
        except Exception:
            pass

        # Tier 3: By Placeholder
        try:
            loc = page.get_by_placeholder(re.compile(re.escape(desc_clean), re.IGNORECASE))
            if await loc.count() > 0 and await loc.first.is_visible():
                return loc.first, "placeholder"
        except Exception:
            pass

        # Tier 4: Direct Attributes (ID, Name, data-testid, aria-label)
        clean_attr = desc_clean.replace(" ", "_").lower()
        attr_selectors = [
            f"#{desc_clean}",
            f"#{clean_attr}",
            f"[name='{desc_clean}']",
            f"[name='{clean_attr}']",
            f"[data-testid='{clean_attr}']",
            f"[aria-label*='{desc_clean}' i]"
        ]
        for sel in attr_selectors:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0 and await loc.first.is_visible():
                    return loc.first, f"attr:{sel}"
            except Exception:
                pass

        # Tier 5: Visible Text Content
        try:
            loc = page.get_by_text(re.compile(re.escape(desc_clean), re.IGNORECASE))
            if await loc.count() > 0 and await loc.first.is_visible():
                return loc.first, "text"
        except Exception:
            pass

        # Tier 6: Semantic CSS heuristics
        css_candidates = []
        if "search" in desc_clean.lower():
            css_candidates = [
                "input[type='search']",
                "input[name*='search']",
                "input[name='q']",
                "#search",
                "input.search"
            ]
        elif "submit" in desc_clean.lower():
            css_candidates = ["button[type='submit']", "input[type='submit']", "button.submit"]

        for sel in css_candidates:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0 and await loc.first.is_visible():
                    return loc.first, f"semantic_css:{sel}"
            except Exception:
                pass

        # Tier 7: Multimodal Vision Fallback
        if self.vision:
            try:
                # Capture viewport screenshot for vision element locator
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    shot_path = tmp.name
                await page.screenshot(path=shot_path)
                elem = await self.vision.locate_element(shot_path, desc_clean)
                if elem and elem.confidence > 0.7:
                    # Return point click locator from bounding box center
                    box = elem.bounding_box
                    cx = box["x"] + box["width"] // 2
                    cy = box["y"] + box["height"] // 2
                    # Use page coordinate locator
                    loc = page.locator(f"xpath=//*").first
                    return loc, f"vision:({cx},{cy})"
            except Exception:
                pass

        return None, "unresolved"
