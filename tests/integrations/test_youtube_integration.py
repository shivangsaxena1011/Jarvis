"""
Unit & Integration Tests for SHIVANI YouTube Integration & Tools.
"""

import pytest
from integrations.youtube.service import YouTubeService
from tools.integrations.youtube_tools import (
    YouTubeSearchTool,
    YouTubeOpenVideoTool,
    YouTubePlayTool,
    YouTubePauseTool,
    YouTubeStopTool,
    YouTubeGetCurrentVideoTool,
)
from agents.browser.agent import BrowserAgent


@pytest.mark.asyncio
async def test_youtube_search_ranking():
    """Verify YouTubeService ranks matching songs, boosts official channels, and filters."""
    service = YouTubeService()
    res = await service.search(query="Arijit Singh Tum Hi Ho", limit=5)
    
    assert res["status"] == "success"
    assert res["count"] > 0
    results = res["results"]
    assert len(results) <= 5
    
    # Top result should be the highest scored
    assert results[0]["score"] >= results[-1]["score"]
    assert any("arijit" in r["title"].lower() or "tum hi ho" in r["title"].lower() for r in results)


@pytest.mark.asyncio
async def test_youtube_playback_controls():
    """Verify play, pause, stop and get_current_video lifecycle."""
    service = YouTubeService()
    
    # Open video
    open_res = await service.open_video("Tum Hi Ho")
    assert open_res["status"] == "playing"
    assert open_res["playback_verified"] is True
    
    # Check current video
    cur = await service.get_current_video()
    assert cur["status"] == "playing"
    assert "video_id" in cur
    
    # Pause
    pause_res = await service.pause()
    assert pause_res["status"] == "paused"
    
    # Play
    play_res = await service.play()
    assert play_res["status"] == "resumed"
    
    # Stop
    stop_res = await service.stop()
    assert stop_res["status"] == "stopped"


@pytest.mark.asyncio
async def test_youtube_registered_tools():
    """Verify all registered YouTube tools execute and verify cleanly."""
    service = YouTubeService()
    
    search_tool = YouTubeSearchTool(youtube_service=service)
    open_tool = YouTubeOpenVideoTool(youtube_service=service)
    play_tool = YouTubePlayTool(youtube_service=service)
    pause_tool = YouTubePauseTool(youtube_service=service)
    stop_tool = YouTubeStopTool(youtube_service=service)
    status_tool = YouTubeGetCurrentVideoTool(youtube_service=service)
    
    # 1. Search tool
    s_res = await search_tool.run(query="Kesariya", limit=3)
    s_ver = await search_tool.verify(s_res)
    assert s_ver["verified"] is True
    
    # 2. Open tool
    o_res = await open_tool.run(video_url_or_title="Kesariya")
    o_ver = await open_tool.verify(o_res)
    assert o_ver["verified"] is True
    
    # 3. Status tool
    st_res = await status_tool.run()
    st_ver = await status_tool.verify(st_res)
    assert st_ver["verified"] is True
    
    # 4. Pause & Play & Stop
    p_res = await pause_tool.run()
    assert (await pause_tool.verify(p_res))["verified"] is True
    
    pl_res = await play_tool.run()
    assert (await play_tool.verify(pl_res))["verified"] is True
    
    sp_res = await stop_tool.run()
    assert (await stop_tool.verify(sp_res))["verified"] is True
