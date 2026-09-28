"""
Unit and integration tests for SHIVANI Computer Agent and Desktop Task Planning.
"""

import pytest
import asyncio
from pathlib import Path

from tools.desktop.os.mock import MockOSAdapter
from agents.computer.agent import ComputerAgent
from agents.computer.context import CurrentUIContext
from agents.computer.observer import ScreenObserver
from agents.computer.observation import DesktopObservation
from agents.computer.vision import MockVisionProvider
from agents.computer.browser_stub import BrowserAgent
from core.orchestrator.orchestrator import Orchestrator
from core.tasks.task import TaskStatus
from core.orchestrator.state_machine import TaskState


@pytest.fixture
def agent_setup(tmp_path):
    adapter = MockOSAdapter()
    ctx = CurrentUIContext()
    agent = ComputerAgent(adapter=adapter, context=ctx, vision_provider=MockVisionProvider())
    return adapter, ctx, agent


@pytest.mark.asyncio
async def test_screen_observer_and_context(agent_setup):
    adapter, ctx, agent = agent_setup

    # 1. Observation
    obs = await agent.observe(capture_image=True)
    assert isinstance(obs, DesktopObservation)
    assert obs.active_window == "Visual Studio Code - Shivani"
    assert obs.screen.width == 1920
    assert len(obs.elements) > 0

    # 2. Context updated automatically
    assert ctx.active_window == "Visual Studio Code - Shivani"
    assert ctx.last_screenshot is not None
    assert ctx.get_deictic_target() == "Visual Studio Code - Shivani"


@pytest.mark.asyncio
async def test_computer_agent_actions(agent_setup):
    adapter, ctx, agent = agent_setup

    # Open App
    open_res = await agent.open_app("notepad")
    assert open_res["process_verified"] is True
    assert open_res["window_verified"] is True

    # Focus Window
    focus_res = await agent.focus_window("Chrome")
    assert focus_res["verified"] is True

    # Safe Type
    type_res = await agent.safe_type("search artificial intelligence", target_window="Chrome")
    assert type_res["success"] is True

    # Minimize Window
    min_res = await agent.minimize_window("Chrome")
    assert min_res["verified"] is True

    # Close App
    close_res = await agent.close_app("notepad")
    assert close_res["verified"] is True


@pytest.mark.asyncio
async def test_browser_agent_detection(agent_setup):
    adapter, _, agent = agent_setup
    browser = BrowserAgent(adapter)

    detected = await browser.detect_installed_browsers()
    assert "chrome" in detected
    assert detected["chrome"] is not None


@pytest.mark.asyncio
async def test_action_recovery_with_retries(agent_setup):
    adapter, _, agent = agent_setup

    call_count = 0

    async def flaky_action():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("Transient device lock")
        return {"recovered": True}

    res = await agent.execute_with_recovery(flaky_action, max_retries=3, action_name="flaky_test")
    assert res["recovered"] is True
    assert call_count == 2


@pytest.mark.asyncio
async def test_orchestrator_desktop_tasks():
    mock_os = MockOSAdapter()
    orch = Orchestrator(os_adapter=mock_os)

    # 1. "Shivani, open VS Code."
    task_code = await orch.submit_task("Shivani, open VS Code.")
    while task_code.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
        await asyncio.sleep(0.1)
    assert task_code.status == TaskStatus.COMPLETED

    # 2. "Shivani, minimize Chrome."
    task_min = await orch.submit_task("Shivani, minimize Chrome.")
    while task_min.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
        await asyncio.sleep(0.1)
    assert task_min.status == TaskStatus.COMPLETED

    # 3. "Shivani, switch to VS Code."
    task_switch = await orch.submit_task("Shivani, switch to VS Code.")
    while task_switch.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
        await asyncio.sleep(0.1)
    assert task_switch.status == TaskStatus.COMPLETED

    # 4. "Shivani, open my Downloads folder."
    task_down = await orch.submit_task("Shivani, open my Downloads folder.")
    while task_down.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
        await asyncio.sleep(0.1)
    assert task_down.status == TaskStatus.COMPLETED

    # 5. "Shivani, find my PDF files."
    task_pdf = await orch.submit_task("Shivani, find my PDF files.")
    while task_pdf.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
        await asyncio.sleep(0.1)
    assert task_pdf.status == TaskStatus.COMPLETED

    # 6. "Shivani, close Chrome."
    task_close = await orch.submit_task("Shivani, close Chrome.")
    while task_close.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
        await asyncio.sleep(0.1)
    assert task_close.status == TaskStatus.COMPLETED

    # 7. "Shivani, take a screenshot."
    task_shot = await orch.submit_task("Shivani, take a screenshot.")
    while task_shot.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
        await asyncio.sleep(0.1)
    assert task_shot.status == TaskStatus.COMPLETED

    # 8. Emergency Stop ("Shivani stop")
    stopped = orch.stop_all()
    assert orch.emergency.is_stopped is True
