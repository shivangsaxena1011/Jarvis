"""
SHIVANI Multi-Agent Coordination & Concurrency Test Suite
Verifies:
- AgentRegistry metadata and capability matching
- Inter-agent messaging contract and dispatch
- TaskDecomposer DAG generation and dependency progression
- ResourceManager mutual exclusion locks (files, repos, devices)
- Multi-agent goal orchestration
"""

import asyncio
import pytest
from core.agents import (
    AgentRegistry,
    AgentDescriptor,
    TaskDecomposer,
    TaskDAG,
    SubTask,
    TaskStage,
    AgentMessage,
    AgentMessageType,
    AgentResponse,
)
from core.concurrency.resource_manager import ResourceManager, LockAcquisitionTimeout
from core.orchestrator.orchestrator import Orchestrator


def test_agent_registry_and_intent_matching():
    registry = AgentRegistry()

    registry.register_agent(
        AgentDescriptor(
            name="coding_agent",
            description="Software engineering agent",
            capabilities=["code", "git", "tests"],
            keywords=["code", "git", "bug", "patch"],
            risk_tier="SENSITIVE",
        ),
        instance=object(),
    )
    registry.register_agent(
        AgentDescriptor(
            name="phone_agent",
            description="Android control agent",
            capabilities=["android", "touch"],
            keywords=["phone", "mobile", "android"],
            risk_tier="SAFE",
        ),
        instance=object(),
    )

    assert registry.get_agent("coding_agent") is not None
    assert registry.match_agent("Fix the login bug in auth.py") == "coding_agent"
    assert registry.match_agent("Phone pe Instagram kholo") == "phone_agent"


@pytest.mark.asyncio
async def test_agent_message_dispatch():
    registry = AgentRegistry()

    async def mock_handler(msg: AgentMessage) -> AgentResponse:
        assert msg.sender == "orchestrator"
        assert msg.payload.get("target") == "auth.py"
        return AgentResponse.success(summary="Bug analyzed successfully", artifacts=["auth.py"])

    registry.register_agent(
        AgentDescriptor(name="coding_agent", description="Coding agent"),
        instance=object(),
        message_handler=mock_handler,
    )

    msg = AgentMessage(
        sender="orchestrator",
        recipient="coding_agent",
        message_type=AgentMessageType.REQUEST,
        payload={"target": "auth.py"},
    )
    resp = await registry.dispatch_message(msg)
    assert resp.status == "success"
    assert "Bug analyzed" in resp.summary
    assert "auth.py" in resp.artifacts


def test_task_decomposer_dag_dependencies():
    # Composite request involving research, implementation, testing, and presentation
    query = "Research AI agents, implement a prototype scraper, run tests, and create a pitch deck"
    dag = TaskDecomposer.decompose(query)

    assert len(dag.subtasks) >= 3
    # Check that first subtask is RESEARCH with no dependencies
    research_sub = next(s for s in dag.subtasks if s.stage == TaskStage.RESEARCH)
    assert len(research_sub.dependencies) == 0

    # Ready subtasks initially should only be the ones with 0 dependencies
    ready = dag.get_ready_subtasks()
    assert len(ready) == 1
    assert ready[0].id == research_sub.id

    # Mark research completed
    dag.mark_completed(research_sub.id, AgentResponse.success("Research completed"))

    # Now coding subtask should be ready
    next_ready = dag.get_ready_subtasks()
    assert len(next_ready) >= 1
    coding_sub = next(s for s in dag.subtasks if s.stage == TaskStage.IMPLEMENTATION)
    assert coding_sub.id in [s.id for s in next_ready]


@pytest.mark.asyncio
async def test_resource_manager_file_locking():
    mgr = ResourceManager()
    test_file = "c:/Users/Project/Jarvis/test_lock_file.txt"

    assert not mgr.is_locked("file", test_file)

    async with mgr.lock_file(test_file, holder="agent_1"):
        assert mgr.is_locked("file", test_file)
        info = mgr.get_lock_info("file", test_file)
        assert info is not None
        assert info["holder"] == "agent_1"

        # Attempt to acquire same lock with short timeout should fail
        with pytest.raises(LockAcquisitionTimeout):
            async with mgr.lock_file(test_file, holder="agent_2", timeout=0.1):
                pass

    # Once released, is_locked is False
    assert not mgr.is_locked("file", test_file)


@pytest.mark.asyncio
async def test_resource_manager_repo_and_device_locking():
    mgr = ResourceManager()
    repo_path = "c:/Users/Project/Jarvis"
    device_id = "shivani-phone-001"

    async with mgr.lock_repository(repo_path, holder="coding_agent"):
        assert mgr.is_locked("repo", repo_path)

    async with mgr.lock_device(device_id, holder="phone_agent"):
        assert mgr.is_locked("device", device_id)


@pytest.mark.asyncio
async def test_submit_multi_agent_goal_orchestration():
    from memory import MemoryManager
    orchestrator = Orchestrator(memory_manager=MemoryManager(db_path=":memory:"))
    # Simple composite goal that runs mock tasks
    dag = await orchestrator.submit_multi_agent_goal("Research AI security and write docs")
    assert dag.is_all_completed()
    assert len(dag.subtasks) >= 2
    for st in dag.subtasks:
        assert st.status == "completed"
