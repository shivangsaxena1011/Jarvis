"""
Master Cross-Application Workflow Tests for SHIVANI.
Implements the 3 canonical multi-agent cross-application scenarios:
1. Local Project to LinkedIn Showcase (Project + Content + LinkedIn DRAFT -> Approval -> Publish)
2. Gmail Triage & Cleanup (Gmail + Categorization + Executive Summary + Cleanup Proposal -> Approval -> Archive)
3. Multi-Source Web & Paper Research (Web Search + Citation Extraction + Structured Synthesis + Markdown/JSON Report)
"""

import pytest
from pathlib import Path
from core.orchestrator.orchestrator import Orchestrator
from core.workflows.cross_app_recipes import create_project_to_linkedin_workflow, create_gmail_triage_workflow, create_research_workflow
from core.workflows.models import WorkflowStatus
from core.projects.models import ProjectMetadata


@pytest.fixture
def test_orchestrator():
    orch = Orchestrator()
    return orch


@pytest.mark.asyncio
async def test_scenario_1_project_to_linkedin_master_flow(test_orchestrator, tmp_path):
    """
    Scenario 1:
    Local project detection -> Content synthesis -> LinkedIn Draft creation ->
    Pause for human approval -> Resumption on approval -> Publication verified.
    """
    orch = test_orchestrator
    
    # 1. Setup a test project in an authorized root
    proj_dir = tmp_path / "HeartDiseaseML"
    proj_dir.mkdir()
    readme = proj_dir / "README.md"
    readme.write_text("# Heart Disease Prediction System\n\nPredictive machine learning pipeline for cardiovascular risk assessment using Random Forest.", encoding="utf-8")
    
    # Register project with indexer
    meta = ProjectMetadata(
        name="HeartDiseaseML",
        path=str(proj_dir),
        readme_summary="Predictive machine learning pipeline for cardiovascular risk assessment.",
        frameworks=["Python", "Scikit-Learn", "FastAPI"],
        key_features=["92% Validation Accuracy", "REST API endpoint", "Interactive risk dashboard"],
        git_remote="https://github.com/developer/heart-disease-ml"
    )
    orch.project_indexer._projects_cache["heartdiseaseml"] = meta
    
    # 2. Build Recipe Workflow
    wf = create_project_to_linkedin_workflow(project_name="HeartDiseaseML")
    
    # 3. Execute Workflow - must pause at LinkedIn publish step
    res1 = await orch.submit_workflow(wf)
    
    assert res1.status == WorkflowStatus.WAITING_FOR_APPROVAL
    assert res1.pending_approval_id is not None
    assert res1.current_step == 3  # Paused at step 3 (publish)
    assert wf.steps[0].status == "COMPLETED"  # project.find
    assert wf.steps[1].status == "COMPLETED"  # content.generate_linkedin_post
    assert wf.steps[2].status == "COMPLETED"  # linkedin.prepare_post (DRAFT)
    
    # Context data must contain draft details
    assert "draft_id" in res1.final_data
    assert res1.final_data["draft_id"].startswith("li_post_")
    assert "content" in res1.final_data
    assert "HeartDiseaseML" in res1.final_data["content"]
    
    # 4. User approves publication
    res2 = await orch.resume_workflow(wf.id, approved=True)
    
    assert res2.status == WorkflowStatus.COMPLETED
    assert wf.steps[3].status == "COMPLETED"
    assert res2.final_data["status"] == "PUBLISHED"
    assert res2.final_data["verified"] is True


@pytest.mark.asyncio
async def test_scenario_2_gmail_triage_and_cleanup_master_flow(test_orchestrator):
    """
    Scenario 2:
    Gmail Read -> Executive Summarization -> Cleanup Proposal -> Pause -> Archive.
    """
    orch = test_orchestrator
    
    wf = create_gmail_triage_workflow(max_age_days=30)
    
    # 1. Execute initial triage & proposal
    res1 = await orch.submit_workflow(wf)
    
    assert res1.status == WorkflowStatus.WAITING_FOR_APPROVAL
    assert res1.pending_approval_id is not None
    assert wf.steps[0].status == "COMPLETED"  # gmail.summarize
    assert wf.steps[1].status == "COMPLETED"  # gmail.cleanup_proposal
    
    # Check summary and proposal generated
    assert "summary_text" in res1.final_data
    assert "proposal_id" in res1.final_data
    assert res1.final_data["proposal_id"].startswith("clean_")
    
    # 2. User approves cleanup
    res2 = await orch.resume_workflow(wf.id, approved=True)
    
    assert res2.status == WorkflowStatus.COMPLETED
    assert wf.steps[2].status == "COMPLETED"
    assert res2.final_data["action_taken"] == "archive"


@pytest.mark.asyncio
async def test_scenario_3_autonomous_research_workflow_master_flow(test_orchestrator, tmp_path):
    """
    Scenario 3:
    Search -> Synthesize -> Save Report (report.md, sources.json, summary.json).
    """
    orch = test_orchestrator
    out_dir = str(tmp_path / "research_bundle")
    
    wf = create_research_workflow(topic="Generative AI Agents", output_dir=out_dir)
    
    res = await orch.submit_workflow(wf)
    
    assert res.status == WorkflowStatus.COMPLETED
    assert wf.steps[0].status == "COMPLETED"  # research.search
    assert wf.steps[1].status == "COMPLETED"  # research.summarize
    assert wf.steps[2].status == "COMPLETED"  # research.save
    
    # Verify disk artifacts
    report_file = Path(res.final_data["report_path"])
    sources_file = Path(res.final_data["sources_path"])
    summary_file = Path(res.final_data["summary_path"])
    
    assert report_file.exists() and report_file.stat().st_size > 0
    assert sources_file.exists() and sources_file.stat().st_size > 0
    assert summary_file.exists() and summary_file.stat().st_size > 0
