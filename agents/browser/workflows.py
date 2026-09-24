"""
SHIVANI Browser Workflows
Higher-level autonomous workflows for common web tasks:
1. YouTube Search & Playback with Result Disambiguation
2. Multi-Engine Web Search (Google, Bing, DuckDuckGo)
3. Webpage Content Summarization & Noise Filtering
4. Structured Data Extraction (Lists, Products, Prices)
"""

import re
import difflib
from typing import Any, Dict, List, Optional
from playwright.async_api import Page

from agents.browser.actions import BrowserActionExecutor
from agents.browser.verifier import BrowserVerifier


class YouTubeWorkflow:
    """Automates YouTube search, result disambiguation, video page verification, and playback."""

    def __init__(self, actions: BrowserActionExecutor, verifier: BrowserVerifier):
        self.actions = actions
        self.verifier = verifier

    async def execute(self, page: Page, song_or_video_query: str) -> Dict[str, Any]:
        """
        Executes YouTube flow:
        1. Navigate to YouTube
        2. Find search input and search query
        3. Parse results and select most relevant video
        4. Initiate and verify playback
        """
        # 1. Navigate
        await page.goto("https://www.youtube.com", timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)

        # 2. Search
        search_box = page.locator("input#search, input.ytd-searchbox, input[name='search_query']").first
        await search_box.wait_for(state="visible", timeout=10000)
        await search_box.fill(song_or_video_query)
        await search_box.press("Enter")

        # Wait for search results
        await page.wait_for_selector("ytd-video-renderer, a#video-title", timeout=15000)
        await page.wait_for_timeout(1500)

        # 3. Disambiguation & Candidate Selection
        candidates = await self.extract_video_candidates(page)
        selected = self.select_best_candidate(candidates, song_or_video_query)
        if not selected:
            raise RuntimeError(f"No video search results found for: {song_or_video_query}")

        # 4. Navigate to selected video
        await page.goto(selected["href"], timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # 5. Playback initiation
        play_script = """() => {
            const v = document.querySelector('video');
            if (v) {
                if (v.paused) v.play();
                return { playing: !v.paused, currentTime: v.currentTime };
            }
            return { playing: false };
        }"""
        await page.evaluate(play_script)
        await page.wait_for_timeout(1000)

        # 6. Verify playback state
        playback_res = await self.verifier.verify_playback_state(page)

        return {
            "query": song_or_video_query,
            "selected_title": selected["title"],
            "url": page.url,
            "playback_verified": playback_res.get("verified", False),
            "video_details": playback_res.get("details", {}),
            "status": "success"
        }

    async def extract_video_candidates(self, page: Page) -> List[Dict[str, str]]:
        """Extracts candidate video links from search results page."""
        candidates_script = """() => {
            const items = Array.from(document.querySelectorAll('ytd-video-renderer, a#video-title')).slice(0, 8);
            return items.map(el => {
                const titleLink = el.tagName === 'A' ? el : el.querySelector('a#video-title');
                if (!titleLink) return null;
                return {
                    title: (titleLink.innerText || titleLink.getAttribute('title') || '').trim(),
                    href: titleLink.href
                };
            }).filter(x => x && x.title && x.href);
        }"""
        return await page.evaluate(candidates_script)

    def select_best_candidate(self, candidates: List[Dict[str, str]], query: str) -> Optional[Dict[str, str]]:
        """Selects the candidate with the highest lexical and semantic match."""
        best_match = None
        best_score = -1.0
        query_lower = query.lower()

        for c in candidates:
            title_lower = c["title"].lower()
            score = difflib.SequenceMatcher(None, query_lower, title_lower).ratio()
            matched_words = sum(1 for w in query_lower.split() if w in title_lower)
            score += 0.2 * (matched_words / max(1, len(query_lower.split())))
            if score > best_score:
                best_score = score
                best_match = c

        return best_match or (candidates[0] if candidates else None)

    _extract_video_candidates = extract_video_candidates
    _select_best_candidate = select_best_candidate


class SearchWorkflow:
    """Automates general web searches across Google, Bing, or DuckDuckGo."""

    def __init__(self, actions: BrowserActionExecutor, verifier: BrowserVerifier):
        self.actions = actions
        self.verifier = verifier

    async def execute(
        self,
        page: Page,
        query: str,
        engine: str = "google",
        limit: int = 5
    ) -> Dict[str, Any]:
        urls = {
            "google": f"https://www.google.com/search?q={query}",
            "bing": f"https://www.bing.com/search?q={query}",
            "duckduckgo": f"https://duckduckgo.com/?q={query}",
        }
        target_url = urls.get(engine.lower(), urls["google"])

        await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)

        extract_script = """() => {
            const results = [];
            document.querySelectorAll('div.g, li.b_algo, article.result, .results-container .result').forEach((el, idx) => {
                if (idx < 10) {
                    const h3 = el.querySelector('h3, h2');
                    const link = el.querySelector('a');
                    const snippet = el.innerText || '';
                    if (h3 && link && link.href) {
                        results.push({
                            title: h3.innerText.trim(),
                            url: link.href,
                            snippet: snippet.slice(0, 200).replace(/\\s+/g, ' ').trim()
                        });
                    }
                }
            });
            return results;
        }"""
        items = await page.evaluate(extract_script)

        return {
            "query": query,
            "engine": engine,
            "url": page.url,
            "result_count": len(items),
            "results": items[:limit],
            "verified": len(items) > 0
        }


class SummarizationWorkflow:
    """Extracts prominent content from page, strips navigational noise, and generates structured summary."""

    async def execute(self, page: Page, max_length: int = 2500) -> Dict[str, Any]:
        title = await page.title()
        url = page.url

        text_script = """() => {
            const clone = document.body.cloneNode(true);
            const noise = clone.querySelectorAll('nav, header, footer, script, style, noscript, [role="navigation"], .ad, .advertisement');
            noise.forEach(n => n.remove());
            return (clone.innerText || '').replace(/\\s+/g, ' ').trim();
        }"""
        clean_text = await page.evaluate(text_script)
        truncated_text = clean_text[:max_length]

        # Extract top headings
        headings = await page.evaluate("""() => Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.innerText.trim()).filter(Boolean).slice(0, 8)""")

        # Generate rule-based executive summary
        paragraphs = [p.strip() for p in truncated_text.split('.') if len(p.strip()) > 30]
        summary_sentences = paragraphs[:4]
        summary = '. '.join(summary_sentences) + ('.' if summary_sentences else '')

        return {
            "status": "success",
            "title": title,
            "url": url,
            "headings": headings,
            "summary": summary or truncated_text[:500],
            "total_chars_extracted": len(clean_text)
        }


class ExtractionWorkflow:
    """Extracts structured key-value data, lists, or tables from the active page."""

    async def execute(self, page: Page, extraction_type: str = "general") -> Dict[str, Any]:
        title = await page.title()
        url = page.url

        script = """() => {
            const data = {
                headings: [],
                links: [],
                tables: []
            };
            document.querySelectorAll('h1, h2').forEach(h => {
                if (h.innerText.trim()) data.headings.push(h.innerText.trim());
            });
            document.querySelectorAll('a[href]').forEach((a, i) => {
                if (i < 20 && a.innerText.trim() && a.href.startsWith('http')) {
                    data.links.push({ text: a.innerText.trim(), href: a.href });
                }
            });
            return data;
        }"""
        extracted = await page.evaluate(script)

        return {
            "status": "success",
            "source_url": url,
            "page_title": title,
            "extraction_type": extraction_type,
            "data": extracted
        }

