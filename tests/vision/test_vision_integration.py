"""
End-to-End Integration Tests for Phase 10 Vision Intelligence and Agent Tools.
"""

import pytest
import os
from vision.service import VisionService, get_vision_service
from agents.computer.vision import Phase10VisionProvider
from agents.computer.agent import ComputerAgent
from tools.desktop.screen_tools import (
    VisualInspectTool,
    VisualFindElementTool,
    VisualOCRTool,
)
from tools.desktop.os.mock import MockOSAdapter


@pytest.mark.asyncio
async def test_vision_service_capture_and_understand():
    service = get_vision_service()
    context = service.capture_and_understand()

    assert context.screenshot_path is not None
    assert os.path.exists(context.screenshot_path)
    assert context.monitor is not None
    assert context.elements is not None
    assert context.ui_tree is not None

    # Test debug overlay generation
    overlay_path = service.create_debug_overlay(context)
    assert os.path.exists(overlay_path)


@pytest.mark.asyncio
async def test_phase10_vision_provider_adapter():
    service = get_vision_service()
    ctx = service.capture_and_understand()

    provider = Phase10VisionProvider(vision_service=service)
    analysis = await provider.analyze_screenshot(ctx.screenshot_path)

    assert "elements" in analysis
    assert "detected_text" in analysis

    summary = await provider.describe_screen(ctx.screenshot_path)
    assert len(summary) > 0


@pytest.mark.asyncio
async def test_computer_agent_click_element_by_vision():
    mock_adapter = MockOSAdapter()
    agent = ComputerAgent(adapter=mock_adapter)

    res = await agent.click_element_by_vision("Submit")
    assert "success" in res
    assert res["success"] is True
    assert res["confidence"] > 0.0


@pytest.mark.asyncio
async def test_registered_vision_tools():
    # 1. VisualInspectTool
    inspect_tool = VisualInspectTool()
    insp_res = await inspect_tool.run()
    assert "element_count" in insp_res
    assert "screenshot_path" in insp_res
    insp_ver = await inspect_tool.verify(insp_res)
    assert insp_ver["verified"] is True

    # 2. VisualFindElementTool
    find_tool = VisualFindElementTool()
    find_res = await find_tool.run(query="Submit button")
    assert "found" in find_res
    assert find_res["found"] is True
    assert "click_point" in find_res

    # 3. VisualOCRTool
    ocr_tool = VisualOCRTool()
    ocr_res = await ocr_tool.run()
    assert "words" in ocr_res
    assert ocr_res["word_count"] > 0
