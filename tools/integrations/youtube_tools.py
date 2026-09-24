"""
SHIVANI YouTube Registered Tools
Registered tools exposing YouTube searches, result ranking, playback, and status.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from integrations.youtube.service import YouTubeService
from agents.browser.agent import BrowserAgent


class YouTubeSearchArgs(BaseModel):
    query: str = Field(description="Search keywords or artist/song title")
    limit: int = Field(default=5, description="Maximum number of ranked results to return")


class YouTubeSearchTool(BaseTool):
    name = "youtube.search"
    description = "Search YouTube for videos with ranking by title similarity, artist, and relevance."
    permission_level = RiskLevel.SAFE
    args_schema = YouTubeSearchArgs
    timeout = 30.0

    def __init__(self, youtube_service: Optional[YouTubeService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = youtube_service or YouTubeService(browser_agent or BrowserAgent())

    async def run(self, query: str, limit: int = 5) -> Dict[str, Any]:
        return await self.service.search(query=query, limit=limit)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        count = result_data.get("count", 0)
        return {"verified": count > 0, "results_found": count}


class YouTubeOpenVideoArgs(BaseModel):
    video_url_or_title: str = Field(description="Direct YouTube video URL or title to search and play")


class YouTubeOpenVideoTool(BaseTool):
    name = "youtube.open_video"
    description = "Open and play a specific YouTube video by URL or best search match."
    permission_level = RiskLevel.SAFE
    args_schema = YouTubeOpenVideoArgs
    timeout = 40.0

    def __init__(self, youtube_service: Optional[YouTubeService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = youtube_service or YouTubeService(browser_agent or BrowserAgent())

    async def run(self, video_url_or_title: str) -> Dict[str, Any]:
        return await self.service.open_video(video_url_or_title)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("playback_verified", False), "title": result_data.get("title")}


class YouTubePlayTool(BaseTool):
    name = "youtube.play"
    description = "Resume or play the currently open YouTube video."
    permission_level = RiskLevel.SAFE
    timeout = 10.0

    def __init__(self, youtube_service: Optional[YouTubeService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = youtube_service or YouTubeService(browser_agent or BrowserAgent())

    async def run(self) -> Dict[str, Any]:
        return await self.service.play()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class YouTubePauseTool(BaseTool):
    name = "youtube.pause"
    description = "Pause the currently playing YouTube video."
    permission_level = RiskLevel.SAFE
    timeout = 10.0

    def __init__(self, youtube_service: Optional[YouTubeService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = youtube_service or YouTubeService(browser_agent or BrowserAgent())

    async def run(self) -> Dict[str, Any]:
        return await self.service.pause()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class YouTubeStopTool(BaseTool):
    name = "youtube.stop"
    description = "Stop the YouTube video playback and reset position."
    permission_level = RiskLevel.SAFE
    timeout = 10.0

    def __init__(self, youtube_service: Optional[YouTubeService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = youtube_service or YouTubeService(browser_agent or BrowserAgent())

    async def run(self) -> Dict[str, Any]:
        return await self.service.stop()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class YouTubeGetCurrentVideoTool(BaseTool):
    name = "youtube.get_current_video"
    description = "Get status and details of the currently playing YouTube video."
    permission_level = RiskLevel.SAFE
    timeout = 10.0

    def __init__(self, youtube_service: Optional[YouTubeService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = youtube_service or YouTubeService(browser_agent or BrowserAgent())

    async def run(self) -> Dict[str, Any]:
        return await self.service.get_current_video()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("url"))}
