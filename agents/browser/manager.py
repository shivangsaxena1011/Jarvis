"""
SHIVANI Browser Runtime Manager
Controls the Playwright runtime lifecycle, multi-browser channel selection
(Chrome, Brave, Edge, Chromium), persistent profiles, and page instances.
"""

import sys
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page

from agents.browser.session import BrowserSession
from agents.browser.profile import BrowserProfileManager
from core.config import get_settings


class BrowserManager:
    """Manages Playwright browser instances, channels, contexts, and tabs."""

    def __init__(
        self,
        profile_manager: Optional[BrowserProfileManager] = None,
        session: Optional[BrowserSession] = None,
        headless: Optional[bool] = None,
        download_dir: Optional[Path] = None,
        browser_type: Optional[str] = None,
        use_persistent_profile: bool = False
    ):
        # Enforce WindowsProactorEventLoopPolicy on Windows for child process pipes
        if sys.platform == "win32":
            try:
                if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception:
                pass

        self.settings = get_settings()
        self.profiles = profile_manager or BrowserProfileManager()
        self.session = session or BrowserSession()
        self.headless = headless
        self.download_dir = download_dir or self.settings.download_path
        self.browser_type = browser_type
        self.use_persistent_profile = use_persistent_profile

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._pages: Dict[str, Page] = {}

    async def start(
        self,
        headless: Optional[bool] = None,
        browser_type: Optional[str] = None,
        use_persistent_profile: bool = False
    ) -> Page:
        """Launches browser runtime and opens initial page/tab."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()

        is_headless = headless if headless is not None else (self.headless if self.headless is not None else self.settings.BROWSER_HEADLESS)
        preferred = (browser_type or self.browser_type or self.settings.PREFERRED_BROWSER).lower()
        use_profile = use_persistent_profile or self.use_persistent_profile

        # Determine Playwright launch channel / fallback
        channel = None
        if preferred == "chrome":
            channel = "chrome"
        elif preferred == "edge" or preferred == "msedge":
            channel = "msedge"
        elif preferred == "brave":
            # For Brave, use chrome channel or custom executable if discovered
            channel = "chrome"

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--mute-audio" if is_headless else "--autoplay-policy=no-user-gesture-required",
        ]

        if use_profile or self.settings.BROWSER_USER_DATA_DIR:
            profile_dir = self.profiles.get_profile_path(self.session.profile_name)
            try:
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=is_headless,
                    channel=channel,
                    args=launch_args,
                    timeout=self.settings.BROWSER_NAVIGATION_TIMEOUT * 1000,
                    downloads_path=str(self.settings.download_path)
                )
            except Exception:
                # Fallback to standard chromium without channel
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=is_headless,
                    args=launch_args,
                    timeout=self.settings.BROWSER_NAVIGATION_TIMEOUT * 1000,
                    downloads_path=str(self.settings.download_path)
                )
            pages = self._context.pages
            page = pages[0] if pages else await self._context.new_page()
        else:
            try:
                self._browser = await self._playwright.chromium.launch(
                    headless=is_headless,
                    channel=channel,
                    args=launch_args,
                    timeout=self.settings.BROWSER_NAVIGATION_TIMEOUT * 1000
                )
            except Exception:
                # Fallback to standard bundled Chromium
                self._browser = await self._playwright.chromium.launch(
                    headless=is_headless,
                    args=launch_args,
                    timeout=self.settings.BROWSER_NAVIGATION_TIMEOUT * 1000
                )
            self._context = await self._browser.new_context(
                accept_downloads=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await self._context.new_page()

        tab_id = f"tab_{len(self._pages) + 1}"
        self._pages[tab_id] = page
        self.session.register_tab(tab_id=tab_id, url=page.url, is_active=True)

        return page

    async def get_active_page(self) -> Page:
        """Returns the currently active Playwright page, launching if not already running."""
        if not self._context or not self._pages:
            return await self.start()

        active_id = self.session.active_tab_id
        if active_id and active_id in self._pages:
            return self._pages[active_id]

        first_id = next(iter(self._pages.keys()))
        return self._pages[first_id]

    async def new_tab(self, url: str = "about:blank") -> Page:
        """Opens a new tab and updates session state."""
        if not self._context:
            await self.start()

        page = await self._context.new_page()
        if url and url != "about:blank":
            await page.goto(url, timeout=self.settings.BROWSER_NAVIGATION_TIMEOUT * 1000)

        tab_id = f"tab_{len(self._pages) + 1}"
        self._pages[tab_id] = page
        self.session.register_tab(tab_id=tab_id, url=page.url, title=await page.title(), is_active=True)
        return page

    async def switch_tab(self, identifier: Any) -> Optional[Page]:
        """Switches active focus to target tab."""
        target_id = self.session.switch_tab(identifier)
        if target_id and target_id in self._pages:
            page = self._pages[target_id]
            await page.bring_to_front()
            return page
        return None

    async def close_tab(self, identifier: Optional[Any] = None) -> bool:
        """Closes target or currently active tab."""
        target_id = None
        if identifier is not None:
            if isinstance(identifier, int):
                for tid, tab in self.session.tabs.items():
                    if tab.index == identifier:
                        target_id = tid
                        break
            elif str(identifier) in self._pages:
                target_id = str(identifier)
        else:
            target_id = self.session.active_tab_id

        if target_id and target_id in self._pages:
            page = self._pages.pop(target_id)
            await page.close()
            self.session.remove_tab(target_id)
            return True
        return False

    async def close(self) -> None:
        """Closes all browser contexts and Playwright instances."""
        for p in list(self._pages.values()):
            try:
                await p.close()
            except Exception:
                pass
        self._pages.clear()

        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
