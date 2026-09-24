"""
SHIVANI Browser Interaction Tools
Registered tools for clicking, typing, selecting, finding, and scrolling elements in web pages.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from agents.browser.agent import BrowserAgent


class BrowserFindArgs(BaseModel):
    target: str = Field(description="Natural language description or selector of target element (e.g. 'search button', 'login link')")
    element_type: Optional[str] = Field(default=None, description="Optional element type hint: 'button', 'input', 'link', 'text'")


class BrowserFindTool(BaseTool):
    name = "browser.find"
    description = "Locate an element on the webpage using natural language descriptions or selectors."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserFindArgs
    timeout = 10.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, target: str, element_type: Optional[str] = None) -> Dict[str, Any]:
        return await self.browser_agent.find(target, element_type=element_type)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("found", False), "strategy": result_data.get("strategy")}


class BrowserClickArgs(BaseModel):
    target: str = Field(description="Natural language description, text, or selector of element to click")


class BrowserClickTool(BaseTool):
    name = "browser.click"
    description = "Click an interactive element (button, link, tab, item) on the webpage."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserClickArgs
    timeout = 15.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, target: str) -> Dict[str, Any]:
        return await self.browser_agent.click_element(target)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success", "target": kwargs.get("target")}


class BrowserDoubleClickTool(BaseTool):
    name = "browser.double_click"
    description = "Double click an element on the webpage."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserClickArgs
    timeout = 15.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, target: str) -> Dict[str, Any]:
        return await self.browser_agent.double_click(target)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success"}


class BrowserTypeArgs(BaseModel):
    target: str = Field(description="Natural language description or selector of input element")
    text: str = Field(description="Text to type into the field")
    press_enter: bool = Field(default=False, description="Whether to press Enter after typing")


class BrowserTypeTool(BaseTool):
    name = "browser.type"
    description = "Type text into an input field or textarea on the webpage."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserTypeArgs
    timeout = 15.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, target: str, text: str, press_enter: bool = False) -> Dict[str, Any]:
        return await self.browser_agent.type_text(target=target, text=text, press_enter=press_enter)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success", "characters": result_data.get("characters_typed", 0)}


class BrowserClearArgs(BaseModel):
    target: str = Field(description="Target input element to clear")


class BrowserClearTool(BaseTool):
    name = "browser.clear"
    description = "Clear all text from an input or textarea field."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserClearArgs
    timeout = 10.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, target: str) -> Dict[str, Any]:
        return await self.browser_agent.clear_input(target)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success"}


class BrowserSelectArgs(BaseModel):
    target: str = Field(description="Select/dropdown element description or selector")
    value: str = Field(description="Option value or display text to select")


class BrowserSelectTool(BaseTool):
    name = "browser.select"
    description = "Select an option from a dropdown / select element."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserSelectArgs
    timeout = 15.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, target: str, value: str) -> Dict[str, Any]:
        return await self.browser_agent.select_option(target, value)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success"}


class BrowserPressKeyArgs(BaseModel):
    key: str = Field(description="Key to press (e.g. 'Enter', 'Escape', 'Tab', 'ArrowDown')")


class BrowserPressKeyTool(BaseTool):
    name = "browser.press_key"
    description = "Simulate pressing a keyboard key on the browser page."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserPressKeyArgs
    timeout = 5.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, key: str) -> Dict[str, Any]:
        return await self.browser_agent.press_key(key)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success", "key": kwargs.get("key")}


class BrowserScrollArgs(BaseModel):
    direction: str = Field(default="down", description="Scroll direction: 'up' or 'down'")
    amount: int = Field(default=500, description="Pixel scroll distance")


class BrowserScrollTool(BaseTool):
    name = "browser.scroll"
    description = "Scroll the active webpage up or down."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserScrollArgs
    timeout = 10.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        return await self.browser_agent.scroll(direction=direction, amount=amount)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success"}


class BrowserScrollToArgs(BaseModel):
    x: int = Field(default=0, description="X pixel coordinate")
    y: int = Field(description="Y pixel coordinate")


class BrowserScrollToTool(BaseTool):
    name = "browser.scroll_to"
    description = "Scroll the active webpage to exact coordinate offsets."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserScrollToArgs
    timeout = 10.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, x: int = 0, y: int = 0) -> Dict[str, Any]:
        return await self.browser_agent.scroll_to(x=x, y=y)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success"}
