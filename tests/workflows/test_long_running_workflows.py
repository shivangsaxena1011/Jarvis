"""
Unit & Integration Tests for SHIVANI Long-Running Checkpointed Workflows & Artifact Management.
Tests stage checkpoint creation, persistence, crash resumption, and the unified hackathon recipe.
"""

import pytest
from pathlib import Path
from core.workflows.models import Workflow, WorkflowStep, WorkflowStatus
from core.workflows.engine import WorkflowEngine
from core.workflows.cross_app_recipes import create_hackathon_project_workflow
from core.artifacts.manager import ArtifactManager
from core.orchestrator.orchestrator import Orchestrator
from tools.registry import ToolRegistry
from security.permissions.engine import PermissionEngine, RiskLevel
from core.events.bus import get_event_bus
from tools.base import BaseTool
from pydantic import BaseModel, Field
from typing import Any, Dict


# Stage Test Tools
class StageArgs(BaseModel):
    val: str = Field(default="data")


class Stage1Tool(BaseTool):
    name = "test.stage1"
    description = "Stage 1 research tool"
    permission_level = RiskLevel.SAFE
    args_schema = StageArgs

    async def run(self, val: str = "data") -> Dict[str, Any]:
        return {"research_summary": "Identified core principles", "score": 98}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True}


class Stage2Tool(BaseTool):
    name = "test.stage2"
    description = "Stage 2 architecture tool"
    permission_level = RiskLevel.SAFE
    args_schema = StageArgs

    async def run(self, val: str = "data") -> Dict[str, Any]:
        return {"architecture_spec": "Modular 3-tier architecture", "services": 3}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True}


class Stage3Tool(BaseTool):
    name = "test.stage3"
    description = "Stage 3 implementation tool"
    permission_level = RiskLevel.SAFE
    args_schema = StageArgs

    async def run(self, val: str = "data") -> Dict[str, Any]:
        return {"impl_status": "Built and tested", "files_created": 4}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True}


@pytest.fixture
def checkpoint_engine(tmp_path):
    perms = PermissionEngine()
    reg = ToolRegistry(permission_engine=perms)
    reg.register(Stage1Tool())
    reg.register(Stage2Tool())
    reg.register(Stage3Tool())
    artifacts = ArtifactManager(root_dir=tmp_path / "artifacts")
    engine = WorkflowEngine(tool_registry=reg, permission_engine=perms, event_bus=get_event_bus(), artifact_manager=artifacts)
    return engine, artifacts


@pytest.mark.asyncio
async def test_workflow_stage_checkpointing_and_resumption(checkpoint_engine):
    """Verify stage checkpoints are saved to memory & disk, and execution resumes from checkpoint."""
    engine, artifacts = checkpoint_engine

    wf = Workflow(
        id="wf_ckpt_1",
        name="Stage Checkpoint Test",
        steps=[
            WorkflowStep(id="s1", stage="research", description="Research stage", agent="system", tool="test.stage1", input={}),
            WorkflowStep(id="s2", stage="architecture", description="Architecture stage", agent="system", tool="test.stage2", input={}),
            WorkflowStep(id="s3", stage="implementation", description="Implementation stage", agent="system", tool="test.stage3", input={}),
        ]
    )

    # 1. Execute full workflow
    res = await engine.execute_workflow(wf)
    assert res.status == WorkflowStatus.COMPLETED
    assert "research" in res.completed_stages
    assert "architecture" in res.completed_stages
    assert "implementation" in res.completed_stages

    # Verify checkpoints saved on disk
    ckpt_file = artifacts.get_artifact_path("checkpoints", f"{wf.id}_research.json")
    assert ckpt_file.exists()

    # 2. Test Resumption from Stage Checkpoint
    # Create workflow that only executed stage 1
    wf2 = Workflow(
        id="wf_ckpt_2",
        name="Resumption Test",
        steps=[
            WorkflowStep(id="s1", stage="research", description="Research stage", agent="system", tool="test.stage1", input={}),
            WorkflowStep(id="s2", stage="architecture", description="Architecture stage", agent="system", tool="test.stage2", input={}),
            WorkflowStep(id="s3", stage="implementation", description="Implementation stage", agent="system", tool="test.stage3", input={}),
        ]
    )
    # Manually simulate checkpoint at stage "research"
    wf2.completed_stages = ["research"]
    wf2.checkpoints["research"] = {
        "stage": "research",
        "step_index": 0,
        "context_data": {"research_summary": "Cached findings"}
    }
    engine.register_workflow(wf2)

    # Resume from checkpoint
    resume_res = await engine.resume_from_checkpoint(wf2.id, stage="research")
    assert resume_res.status == WorkflowStatus.COMPLETED
    assert wf2.steps[1].status == "COMPLETED"
    assert wf2.steps[2].status == "COMPLETED"
    assert resume_res.final_data["architecture_spec"] == "Modular 3-tier architecture"


@pytest.mark.asyncio
async def test_unified_hackathon_master_recipe(tmp_path):
    """Verify Recipe 5: create_hackathon_project_workflow runs through all 6 stages."""
    # Setup test project
    proj_dir = tmp_path / "HackathonApp"
    proj_dir.mkdir()
    (proj_dir / "README.md").write_text("# Hackathon App\nAI document parser.", encoding="utf-8")
    (proj_dir / "pyproject.toml").write_text('[project]\nname = "hackathon-app"\ndependencies = ["fastapi"]\n', encoding="utf-8")
    (proj_dir / "main.py").write_text('from fastapi import FastAPI\napp = FastAPI()\n@app.get("/status")\ndef s(): return {"ok": True}\n', encoding="utf-8")

    orch = Orchestrator()

    wf = create_hackathon_project_workflow(
        project_name="HackathonApp",
        project_path=str(proj_dir),
        problem_statement="Automated verification of business documents"
    )

    res = await orch.submit_workflow(wf)
    assert res.status == WorkflowStatus.COMPLETED
    assert res.current_step == 6

    # Verify stage checkpoints recorded
    assert "research" in res.completed_stages
    assert "architecture" in res.completed_stages
    assert "presentation" in res.completed_stages
    assert res.final_data.get("total_slides", 0) > 0
