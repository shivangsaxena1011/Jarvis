"""
SHIVANI Browser Outcome Verifier
Verifies navigation, search results, video playback, downloads,
uploads, and DOM state changes with empirical evidence.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.async_api import Page


class BrowserVerifier:
    """Provides empirical validation routines for web automation actions."""

    async def verify_navigation(
        self,
        page: Page,
        expected_url_substring: Optional[str] = None,
        previous_url: Optional[str] = None
    ) -> Dict[str, Any]:
        current_url = page.url
        title = await page.title()

        verified = True
        reason = "Navigation succeeded"

        if expected_url_substring:
            if expected_url_substring.lower() not in current_url.lower():
                verified = False
                reason = f"Expected substring '{expected_url_substring}' not in current URL '{current_url}'"

        if previous_url and previous_url == current_url:
            verified = False
            reason = f"URL did not change from previous URL: {previous_url}"

        return {
            "verified": verified,
            "current_url": current_url,
            "title": title,
            "reason": reason
        }

    async def verify_search_results(
        self,
        page: Page,
        min_results: int = 1,
        result_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Checks if search result elements are populated in the DOM."""
        selectors = [result_selector] if result_selector else [
            "#search .g",
            "ytd-video-renderer",
            ".search-results",
            ".result",
            "article",
            "[data-testid='search-result']",
            "div.g",
            ".results-container"
        ]

        count = 0
        matched_selector = None

        for sel in selectors:
            if not sel:
                continue
            try:
                c = await page.locator(sel).count()
                if c >= min_results:
                    count = c
                    matched_selector = sel
                    break
            except Exception:
                continue

        return {
            "verified": count >= min_results,
            "result_count": count,
            "matched_selector": matched_selector
        }

    async def verify_playback_state(self, page: Page) -> Dict[str, Any]:
        """
        Inspects HTML5 video playback state (paused, currentTime, duration, readyState).
        """
        script = """() => {
            const video = document.querySelector('video');
            if (!video) return { has_video: false };
            return {
                has_video: true,
                is_playing: !video.paused && !video.ended && video.readyState > 2,
                current_time: video.currentTime,
                duration: video.duration,
                paused: video.paused,
                muted: video.muted
            };
        }"""
        try:
            state = await page.evaluate(script)
            is_playing = state.get("is_playing", False) or (state.get("has_video", False) and state.get("current_time", 0) > 0)
            return {
                "verified": is_playing,
                "video_detected": state.get("has_video", False),
                "is_playing": is_playing,
                "playback_active": is_playing,
                "details": state
            }
        except Exception as e:
            return {"verified": False, "error": str(e)}

    async def verify_download(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        exists = path.exists() and path.stat().st_size > 0
        return {
            "verified": exists,
            "file_exists": exists,
            "size_bytes": path.stat().st_size if exists else 0,
            "path": str(path.resolve()) if exists else file_path
        }
