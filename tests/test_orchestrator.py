"""
Integration tests for SHIVANI Central Orchestrator & State Machine.
"""

import asyncio
import pytest
from core.config import Settings
from core.context.normalizer import HinglishNormalizer, SessionContext
from core.orchestrator.orchestrator import Orchestrator
from core.tasks.task import TaskStatus


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
    while task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED) and elapsed < timeout:
        await asyncio.sleep(0.1)
        elapsed += 0.1

    assert task.status == TaskStatus.COMPLETED
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

    task = await orch.submit_task("Shivani, open notepad and inspect active window")
    cancelled = orch.stop_all()
    assert cancelled >= 0

    await asyncio.sleep(0.3)
    assert orch.emergency.is_stopped is True
    assert task.status in (TaskStatus.CANCELLED, TaskStatus.FAILED, TaskStatus.COMPLETED)


@pytest.mark.asyncio
async def test_explicit_task_cancellation(tmp_path):
    settings = Settings(
        LLM_PROVIDER="mock",
        SECURITY_POLICY="lenient",
        AUDIT_LOG_PATH=str(tmp_path / "test_audit.jsonl")
    )
    orch = Orchestrator(settings=settings)

    task = await orch.submit_task("Inspect active window")
    cancelled = orch.cancel_task(task.id)
    assert cancelled is True
    assert task.status == TaskStatus.CANCELLED
