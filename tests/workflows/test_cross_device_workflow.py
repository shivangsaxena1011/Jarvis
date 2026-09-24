"""Tests for cross-device workflows (Phone Photo to LinkedIn Showcase)."""

import pytest
from core.orchestrator.orchestrator import Orchestrator
from core.workflows.cross_app_recipes import create_phone_photo_to_linkedin_workflow
from core.workflows.models import WorkflowStatus


@pytest.mark.asyncio
async def test_cross_device_photo_to_linkedin_flow():
    orchestrator = Orchestrator()

    # Create Recipe 6 workflow
    wf = create_phone_photo_to_linkedin_workflow(
        topic="ET Hackathon AI Agent Project",
        photo_query="hackathon"
    )

    # Execute workflow - should pause at step 4 (publish) awaiting user approval
    res = await orchestrator.submit_workflow(wf)
    assert res.status == WorkflowStatus.WAITING_FOR_APPROVAL
    assert res.pending_approval_id is not None
    assert res.current_step == 4  # Paused at publish step

    # Verify earlier steps completed
    assert wf.steps[0].status == "COMPLETED"  # android.list_photos
    assert wf.steps[1].status == "COMPLETED"  # android.transfer_file
    assert wf.steps[2].status == "COMPLETED"  # content.generate_linkedin_post
    assert wf.steps[3].status == "COMPLETED"  # linkedin.prepare_post

    # Resume workflow with approval
    final_res = await orchestrator.resume_workflow(wf.id, approved=True)
    assert final_res.status == WorkflowStatus.COMPLETED
    assert wf.steps[4].status == "COMPLETED"  # linkedin.publish_post
