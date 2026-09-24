"""
SHIVANI Universal Browser Agent
Master autonomous coordinator for web operations using Playwright.
Executes actions through the OBSERVE -> PLAN -> ACT -> VERIFY cycle.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.async_api import Page

from agents.browser.session import BrowserSession
from agents.browser.profile import BrowserProfileManager
from agents.browser.manager import BrowserManager
from agents.browser.observer import PageObserver, PageObservation
from agents.browser.resolver import ElementResolver
from agents.browser.actions import BrowserActionExecutor
from agents.browser.verifier import BrowserVerifier
from agents.browser.workflows import YouTubeWorkflow, SearchWorkflow, SummarizationWorkflow, ExtractionWorkflow
from agents.computer.vision import VisionProvider


class BrowserAgent:
    """Universal AI Browser Agent for autonomous web interaction."""

    def __init__(
        self,
        manager: Optional[BrowserManager] = None,
        vision_provider: Optional[VisionProvider] = None,
        profile_manager: Optional[BrowserProfileManager] = None,
        session: Optional[BrowserSession] = None
    ):
        self.profiles = profile_manager or BrowserProfileManager()
        self.session = session or BrowserSession()
        self.manager = manager or BrowserManager(profile_manager=self.profiles, session=self.session)
        self.observer = PageObserver()
        self.resolver = ElementResolver(vision_provider=vision_provider)
        self.actions = BrowserActionExecutor(resolver=self.resolver)
        self.verifier = BrowserVerifier()

        # Workflows
        self.youtube = YouTubeWorkflow(actions=self.actions, verifier=self.verifier)
        self.search_engine = SearchWorkflow(actions=self.actions, verifier=self.verifier)
        self.summarizer = SummarizationWorkflow()
        self.extractor = ExtractionWorkflow()

    async def get_active_page(self) -> Page:
        return await self.manager.get_active_page()

    async def observe_page(self) -> PageObservation:
        """Inspects current active webpage returning structured observations."""
        page = await self.get_active_page()
        return await self.observer.observe(page)

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigates to URL and verifies completion."""
        page = await self.get_active_page()
        target_url = url if url.startswith(("http://", "https://", "about:", "file:///")) else f"https://{url}"
        await page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
        v = await self.verifier.verify_navigation(page)
        self.session.update_tab(self.session.active_tab_id or "tab_1", url=page.url, title=await page.title())
        return {
            "url": page.url,
            "title": await page.title(),
            "verified": v["verified"],
            "status": "success"
        }

    async def search(self, query: str, engine: str = "google") -> Dict[str, Any]:
        """Executes search query on Google or other engine."""
        page = await self.get_active_page()
        return await self.search_engine.execute(page, query=query, engine=engine)

    async def click_element(self, target: Any) -> Dict[str, Any]:
        """Clicks element using 7-tier resolver and verifies."""
        page = await self.get_active_page()
        res = await self.actions.click(page, target)
        await page.wait_for_timeout(300)
        return res

    async def type_text(self, target: Any, text: str, press_enter: bool = False) -> Dict[str, Any]:
        """Types text into resolved input."""
        page = await self.get_active_page()
        res = await self.actions.type_text(page, target, text, press_enter=press_enter)
        return res

    async def summarize_page(self) -> Dict[str, Any]:
        """Summarizes content of currently active page."""
        page = await self.get_active_page()
        return await self.summarizer.execute(page)

    async def extract_page_data(self, extraction_type: str = "general") -> Dict[str, Any]:
        """Extracts structured lists/links/data from page."""
        page = await self.get_active_page()
        return await self.extractor.execute(page, extraction_type=extraction_type)

    async def play_youtube(self, query: str) -> Dict[str, Any]:
        """Executes full YouTube search, selection, and playback flow."""
        page = await self.get_active_page()
        return await self.youtube.execute(page, query)

    async def go_back(self) -> Dict[str, Any]:
        """Navigates back in history."""
        page = await self.get_active_page()
        await page.go_back()
        return {"url": page.url, "title": await page.title(), "status": "success"}

    async def go_forward(self) -> Dict[str, Any]:
        """Navigates forward in history."""
        page = await self.get_active_page()
        await page.go_forward()
        return {"url": page.url, "title": await page.title(), "status": "success"}

    async def refresh(self) -> Dict[str, Any]:
        """Refreshes the current active page."""
        page = await self.get_active_page()
        await page.reload()
        return {"url": page.url, "title": await page.title(), "status": "success"}

    async def get_title(self) -> str:
        """Returns the title of the active page."""
        page = await self.get_active_page()
        return await page.title()

    async def get_url(self) -> str:
        """Returns the URL of the active page."""
        page = await self.get_active_page()
        return page.url

    async def find(self, target: Any, element_type: Optional[str] = None) -> Dict[str, Any]:
        """Finds an element using the 7-tier resolver."""
        page = await self.get_active_page()
        loc, strat = await self.resolver.resolve(page, target, element_type=element_type)
        return {
            "found": loc is not None,
            "target": str(target),
            "strategy": strat
        }

    async def double_click(self, target: Any) -> Dict[str, Any]:
        """Double clicks target element."""
        page = await self.get_active_page()
        return await self.actions.double_click(page, target)

    async def clear_input(self, target: Any) -> Dict[str, Any]:
        """Clears text input element."""
        page = await self.get_active_page()
        return await self.actions.clear(page, target)

    async def select_option(self, target: Any, value: str) -> Dict[str, Any]:
        """Selects option in select dropdown."""
        page = await self.get_active_page()
        return await self.actions.select_option(page, target, value)

    async def press_key(self, key: str) -> Dict[str, Any]:
        """Presses a key on the active page."""
        page = await self.get_active_page()
        return await self.actions.press_key(page, key)

    async def scroll(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        """Scrolls the active page."""
        page = await self.get_active_page()
        return await self.actions.scroll(page, direction=direction, amount=amount)

    async def scroll_to(self, x: int, y: int) -> Dict[str, Any]:
        """Scrolls active page to specific coordinates."""
        page = await self.get_active_page()
        return await self.actions.scroll_to(page, x=x, y=y)

    async def upload_file(self, target: Any, file_path: str) -> Dict[str, Any]:
        """Uploads file to file input element."""
        page = await self.get_active_page()
        return await self.actions.upload_file(page, target, file_path)

    async def download_file(self, trigger_target: Any, destination_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Handles download triggered by clicking element."""
        page = await self.get_active_page()
        dest = destination_dir or self.manager.download_dir
        return await self.actions.download_file(page, trigger_target, dest)

    async def extract_text(self, selector: Optional[str] = None) -> str:
        """Extracts text from page or matching selector."""
        page = await self.get_active_page()
        return await self.actions.extract_text(page, selector=selector)

    async def extract_links(self, selector: Optional[str] = None) -> List[Dict[str, str]]:
        """Extracts links matching selector or all page links."""
        page = await self.get_active_page()
        return await self.actions.extract_links(page, selector=selector)

    async def new_tab(self, url: str = "about:blank") -> Page:
        return await self.manager.new_tab(url=url)

    async def switch_tab(self, identifier: Any) -> Optional[Page]:
        return await self.manager.switch_tab(identifier)

    async def close_tab(self, identifier: Optional[Any] = None) -> bool:
        return await self.manager.close_tab(identifier)

    async def list_tabs(self) -> List[Dict[str, Any]]:
        return self.session.list_tabs()

    async def capture_screenshot(self, output_path: Path, full_page: bool = False) -> Dict[str, Any]:
        page = await self.get_active_page()
        return await self.actions.capture_screenshot(page, output_path=output_path, full_page=full_page)

    async def close(self) -> None:
        await self.manager.close()

