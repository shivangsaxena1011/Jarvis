"""
Unit & Integration Tests for SHIVANI Cross-Application Workflow Engine.
Tests sequential chaining, approval pausing, exact resumption without restart, and variable substitution.
"""

import pytest
from core.workflows.models import Workflow, WorkflowStep, WorkflowStatus
from core.workflows.engine import WorkflowEngine
from tools.registry import ToolRegistry
from security.permissions.engine import PermissionEngine, RiskLevel
from core.events.bus import get_event_bus
from tools.base import BaseTool
from pydantic import BaseModel, Field
from typing import Any, Dict


# Dummy tools for workflow unit tests
class Step1Args(BaseModel):
    query: str = Field(default="test")

class Step1Tool(BaseTool):
    name = "test.step1"
    description = "Step 1 dummy tool"
    permission_level = RiskLevel.SAFE
    args_schema = Step1Args

    async def run(self, query: str = "test") -> Dict[str, Any]:
        return {"project_name": "SHIVANI-Core", "version": "1.0.0"}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True}


class Step2Args(BaseModel):
    name: str = Field(description="Project name")

class Step2Tool(BaseTool):
    name = "test.step2"
    description = "Step 2 dummy tool"
    permission_level = RiskLevel.SAFE
    args_schema = Step2Args

    async def run(self, name: str) -> Dict[str, Any]:
        return {"draft_id": f"draft_{name.lower()}", "content": f"Showcasing {name}"}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True}


class Step3PublishArgs(BaseModel):
    draft_id: str = Field(description="Draft ID to publish")

class Step3PublishTool(BaseTool):
    name = "test.step3_publish"
    description = "Step 3 publish tool requiring human approval"
    permission_level = RiskLevel.CRITICAL
    args_schema = Step3PublishArgs
    requires_confirmation = True

    async def run(self, draft_id: str) -> Dict[str, Any]:
        return {"status": "PUBLISHED", "post_id": f"pub_{draft_id}"}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "PUBLISHED"}


@pytest.fixture
def workflow_setup():
    perms = PermissionEngine()
    registry = ToolRegistry(permission_engine=perms)
    registry.register(Step1Tool())
    registry.register(Step2Tool())
    registry.register(Step3PublishTool())
    engine = WorkflowEngine(tool_registry=registry, permission_engine=perms, event_bus=get_event_bus())
    return engine


@pytest.mark.asyncio
async def test_workflow_sequential_and_substitution(workflow_setup):
    """Verify workflow steps execute sequentially and resolve template variables ({var})."""
    engine = workflow_setup
    
    wf = Workflow(
        id="wf_seq_1",
        name="Sequential Test",
        description="Test step 1 and step 2",
        steps=[
            WorkflowStep(id="s1", description="Step 1", agent="system", tool="test.step1", input={"query": "Jarvis"}),
            WorkflowStep(id="s2", description="Step 2", agent="system", tool="test.step2", input={"name": "{project_name}"})
        ]
    )
    
    res = await engine.execute_workflow(wf)
    
    assert res.status == WorkflowStatus.COMPLETED
    assert res.current_step == 2
    assert "project_name" in res.final_data
    assert res.final_data["project_name"] == "SHIVANI-Core"
    assert res.final_data["draft_id"] == "draft_shivani-core"


@pytest.mark.asyncio
async def test_workflow_pause_and_resumption(workflow_setup):
    """Verify workflow pauses at step requiring approval and resumes from that exact step without restarting."""
    engine = workflow_setup
    
    wf = Workflow(
        id="wf_pause_1",
        name="Approval Test",
        description="Test pause on critical step",
        steps=[
            WorkflowStep(id="s1", description="Step 1", agent="system", tool="test.step1", input={"query": "Jarvis"}),
            WorkflowStep(id="s2", description="Step 2", agent="system", tool="test.step2", input={"name": "{project_name}"}),
            WorkflowStep(id="s3", description="Step 3", agent="system", tool="test.step3_publish", input={"draft_id": "{draft_id}"}, permission=RiskLevel.CRITICAL, requires_approval=True)
        ]
    )
    
    # 1. First execution should run s1, s2, then pause at s3
    res1 = await engine.execute_workflow(wf)
    
    assert res1.status == WorkflowStatus.WAITING_FOR_APPROVAL
    assert res1.current_step == 2  # Paused at step index 2 (s3)
    assert wf.steps[0].status == "COMPLETED"
    assert wf.steps[1].status == "COMPLETED"
    assert wf.pending_approval_id is not None
    
    # Verify prior results are preserved
    assert res1.final_data["draft_id"] == "draft_shivani-core"
    
    # 2. Resume with rejection -> should cancel
    wf_reject = Workflow(
        id="wf_pause_2",
        name="Approval Rejection Test",
        description="Test rejection on critical step",
        steps=[
            WorkflowStep(id="s1", description="Step 1", agent="system", tool="test.step1", input={}),
            WorkflowStep(id="s2", description="Step 2", agent="system", tool="test.step3_publish", input={"draft_id": "draft_1"}, permission=RiskLevel.CRITICAL, requires_approval=True)
        ]
    )
    res_pause = await engine.execute_workflow(wf_reject)
    assert res_pause.status == WorkflowStatus.WAITING_FOR_APPROVAL
    
    res_rejected = await engine.resume_workflow(wf_reject.id, approved=False)
    assert res_rejected.status == WorkflowStatus.CANCELLED
    
    # 3. Resume the first workflow with approval -> should complete s3 without re-running s1 or s2
    res_resumed = await engine.resume_workflow(wf.id, approved=True)
    assert res_resumed.status == WorkflowStatus.COMPLETED
    assert wf.steps[2].status == "COMPLETED"
    assert res_resumed.final_data["status"] == "PUBLISHED"
    assert res_resumed.final_data["post_id"] == "pub_draft_shivani-core"
