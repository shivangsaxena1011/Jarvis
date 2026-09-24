"""
SHIVANI Browser Action Executor
Executes verified atomic browser operations: clicking, typing, selecting,
scrolling, uploading files, downloading files, and taking page screenshots.
"""

import os
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.async_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

from agents.browser.resolver import ElementResolver


class BrowserActionExecutor:
    """Executes robust, verified DOM interactions using Playwright and ElementResolver."""

    def __init__(self, resolver: Optional[ElementResolver] = None):
        self.resolver = resolver or ElementResolver()

    async def _resolve_target(self, page: Page, target: Any, element_type: Optional[str] = None) -> Locator:
        """Resolves target either as an existing Locator or natural language description."""
        if isinstance(target, Locator):
            return target
        if isinstance(target, str):
            # Check if direct CSS/XPath selector
            if target.startswith(("#", ".", "[", "xpath=", "//")):
                try:
                    loc = page.locator(target)
                    if await loc.count() > 0:
                        return loc.first
                except Exception:
                    pass

            # Resolve through natural language resolver
            loc, strategy = await self.resolver.resolve(page, target, element_type=element_type)
            if loc:
                return loc

            # Fallback to direct locator
            return page.locator(target).first

        raise ValueError(f"Invalid target specification: {target}")

    async def click(self, page: Page, target: Any, timeout: float = 10000) -> Dict[str, Any]:
        loc = await self._resolve_target(page, target, element_type="button")
        await loc.wait_for(state="visible", timeout=timeout)
        await loc.click(timeout=timeout)
        return {"action": "click", "target": str(target), "status": "success"}

    async def double_click(self, page: Page, target: Any, timeout: float = 10000) -> Dict[str, Any]:
        loc = await self._resolve_target(page, target)
        await loc.wait_for(state="visible", timeout=timeout)
        await loc.dblclick(timeout=timeout)
        return {"action": "double_click", "target": str(target), "status": "success"}

    async def type_text(
        self,
        page: Page,
        target: Any,
        text: str,
        clear_first: bool = True,
        press_enter: bool = False,
        timeout: float = 10000
    ) -> Dict[str, Any]:
        loc = await self._resolve_target(page, target, element_type="input")
        await loc.wait_for(state="visible", timeout=timeout)
        if clear_first:
            await loc.fill("")
        await loc.fill(text, timeout=timeout)
        if press_enter:
            await loc.press("Enter")
        return {
            "action": "type",
            "target": str(target),
            "characters_typed": len(text),
            "pressed_enter": press_enter,
            "status": "success"
        }

    async def clear(self, page: Page, target: Any, timeout: float = 10000) -> Dict[str, Any]:
        loc = await self._resolve_target(page, target, element_type="input")
        await loc.wait_for(state="visible", timeout=timeout)
        await loc.fill("", timeout=timeout)
        return {"action": "clear", "target": str(target), "status": "success"}

    async def select_option(self, page: Page, target: Any, value_or_label: str, timeout: float = 10000) -> Dict[str, Any]:
        loc = await self._resolve_target(page, target)
        await loc.wait_for(state="visible", timeout=timeout)
        try:
            await loc.select_option(label=value_or_label, timeout=timeout)
        except Exception:
            await loc.select_option(value=value_or_label, timeout=timeout)
        return {"action": "select", "target": str(target), "value": value_or_label, "status": "success"}

    async def press_key(self, page: Page, key: str, timeout: float = 5000) -> Dict[str, Any]:
        await page.keyboard.press(key)
        return {"action": "press_key", "key": key, "status": "success"}

    async def scroll(self, page: Page, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        delta_y = amount if direction == "down" else -amount
        await page.mouse.wheel(0, delta_y)
        await page.wait_for_timeout(250)
        return {"action": "scroll", "direction": direction, "amount": amount, "status": "success"}

    async def scroll_to(self, page: Page, x: int, y: int) -> Dict[str, Any]:
        await page.evaluate(f"window.scrollTo({x}, {y})")
        return {"action": "scroll_to", "x": x, "y": y, "status": "success"}

    async def upload_file(self, page: Page, target: Any, file_path: str, timeout: float = 10000) -> Dict[str, Any]:
        path_obj = Path(file_path).resolve()
        if not path_obj.exists():
            raise FileNotFoundError(f"File to upload not found: {file_path}")

        loc = await self._resolve_target(page, target, element_type="input")
        await loc.set_input_files(str(path_obj), timeout=timeout)
        return {"action": "upload", "file": str(path_obj), "status": "success"}

    async def download_file(
        self,
        page: Page,
        trigger_target: Any,
        destination_dir: Path,
        timeout: float = 30000
    ) -> Dict[str, Any]:
        destination_dir.mkdir(parents=True, exist_ok=True)
        loc = await self._resolve_target(page, trigger_target)

        async with page.expect_download(timeout=timeout) as download_info:
            await loc.click()

        download = await download_info.value
        file_name = download.suggested_filename
        dest_path = destination_dir / file_name
        await download.save_as(str(dest_path))

        return {
            "action": "download",
            "suggested_filename": file_name,
            "destination_path": str(dest_path.resolve()),
            "size_bytes": os.path.getsize(dest_path),
            "status": "success"
        }

    async def capture_screenshot(
        self,
        page: Page,
        output_path: Path,
        full_page: bool = False
    ) -> Dict[str, Any]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(output_path), full_page=full_page)
        return {
            "path": str(output_path.resolve()),
            "full_page": full_page,
            "size_bytes": os.path.getsize(output_path),
            "status": "success"
        }

    async def extract_text(self, page: Page, selector: Optional[str] = None) -> str:
        if selector:
            loc = page.locator(selector)
            if await loc.count() > 0:
                return (await loc.first.inner_text()).strip()
        return (await page.inner_text("body")).strip()

    async def extract_links(self, page: Page, selector: Optional[str] = None) -> List[Dict[str, str]]:
        base_sel = selector or "a[href]"
        script = f"""() => Array.from(document.querySelectorAll('{base_sel}')).map(a => ({{
            text: (a.innerText || a.getAttribute('aria-label') || '').trim(),
            href: a.href
        }})).filter(x => x.text && x.href)"""
        return await page.evaluate(script)
