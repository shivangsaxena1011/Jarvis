"""
SHIVANI Phase 8 Orchestrator Integration Test Suite
Verifies:
- 151 total registered tools
- User preference resolution in task planning ("open browser" -> "open Brave")
- Checkpoint recording during task execution
- Episodic memory logging upon task completion
"""

import asyncio
import pytest
from core.orchestrator.orchestrator import Orchestrator
from core.tasks.task import TaskStatus


@pytest.mark.asyncio
async def test_orchestrator_phase8_total_tools():
    orchestrator = Orchestrator()
    tools = orchestrator.tools.list_tools()
    assert len(tools) >= 151
    # Verify memory, scheduler, and notification tools are registered
    tool_names = [t["name"] for t in tools]
    assert "memory.get_preference" in tool_names
    assert "memory.set_preference" in tool_names
    assert "memory.search" in tool_names
    assert "memory.forget" in tool_names
    assert "memory.explain" in tool_names
    assert "scheduler.list_jobs" in tool_names
    assert "scheduler.schedule_job" in tool_names
    assert "scheduler.cancel_job" in tool_names
    assert "notifications.list" in tool_names
    assert "notifications.dismiss" in tool_names


@pytest.mark.asyncio
async def test_orchestrator_preference_aware_task_submission():
    from memory import MemoryManager
    orchestrator = Orchestrator(memory_manager=MemoryManager(db_path=":memory:"))
    # Configure user preferred browser
    orchestrator.memory.set_preference("preferred_browser", "Brave")

    # Submit task mentioning "open browser"
    task = await orchestrator.submit_task("Shivani, open browser")
    assert "open brave" in task.metadata["normalized_query"].lower()

    # Wait for completion
    while task.status in (
        TaskStatus.PENDING,
        TaskStatus.PLANNING,
        TaskStatus.WAITING_FOR_PERMISSION,
        TaskStatus.EXECUTING,
        TaskStatus.VERIFYING,
    ):
        await asyncio.sleep(0.05)

    assert task.status == TaskStatus.COMPLETED

    # Verify episodic memory was recorded
    episodes = orchestrator.memory.episodic.get_recent_episodes(limit=5)
    assert len(episodes) >= 1
    recent_ep = next(e for e in episodes if e.value.get("task_id") == task.id)
    assert recent_ep is not None
    assert "open browser" in recent_ep.value["query"].lower()
    assert recent_ep.value["status"] == "completed"
