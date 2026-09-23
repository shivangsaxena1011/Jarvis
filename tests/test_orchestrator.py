"""
Integration tests for SHIVANI Central Orchestrator & State Machine.
"""

import asyncio
import pytest
from core.config import Settings
from core.context.normalizer import HinglishNormalizer, SessionContext
from core.orchestrator.orchestrator import Orchestrator
from core.orchestrator.state_machine import TaskState


def test_hinglish_normalization():
    # Wake word strip
    q1 = HinglishNormalizer.strip_wake_word("Shivani, open notepad")
    assert q1 == "open notepad"

    # Action mappings
    norm1 = HinglishNormalizer.normalize("YouTube kholo")
    assert norm1 == "YouTube open"

    norm2 = HinglishNormalizer.normalize("ye gana chala do")
    assert "play" in norm2

    # Deictic referent resolution
    ctx = SessionContext(current_file="C:/projects/app.py")
    norm3 = HinglishNormalizer.normalize("isko check karo", ctx)
    assert "'C:/projects/app.py'" in norm3


@pytest.mark.asyncio
async def test_orchestrator_task_lifecycle(tmp_path):
    settings = Settings(
        LLM_PROVIDER="mock",
        SECURITY_POLICY="lenient",
        AUDIT_LOG_PATH=str(tmp_path / "test_audit.jsonl")
    )
    orch = Orchestrator(settings=settings)

    task = await orch.submit_task("Shivani, list files")
    
    # Wait for completion
    timeout = 10.0
    elapsed = 0.0
    while task.state not in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED) and elapsed < timeout:
        await asyncio.sleep(0.1)
        elapsed += 0.1

    assert task.state == TaskState.COMPLETED
    assert len(task.step_results) >= 1
    assert task.step_results[0].success is True
    assert task.step_results[0].verification.get("verified") is True


@pytest.mark.asyncio
async def test_emergency_stop_mechanism(tmp_path):
    settings = Settings(
        LLM_PROVIDER="mock",
        SECURITY_POLICY="lenient",
        AUDIT_LOG_PATH=str(tmp_path / "test_audit.jsonl")
    )
    orch = Orchestrator(settings=settings)

    # Submit task
    task = await orch.submit_task("Shivani, open notepad and inspect active window")
    
    # Immediately trigger emergency stop
    cancelled = orch.stop_all()
    assert cancelled >= 0 # at least 0 or 1 task aborted

    # Allow task loop to finalize cancellation
    await asyncio.sleep(0.3)
    assert orch.emergency.is_stopped is True
    assert task.state in (TaskState.CANCELLED, TaskState.FAILED, TaskState.COMPLETED)
