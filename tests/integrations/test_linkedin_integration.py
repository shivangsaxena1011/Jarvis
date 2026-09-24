"""
Unit & Integration Tests for SHIVANI LinkedIn Integration & Tools.
Enforces draft status separation, human approval gates, and content generation.
"""

import pytest
from integrations.linkedin.service import LinkedInService
from agents.content.agent import ContentAgent
from core.projects.models import ProjectMetadata
from tools.integrations.linkedin_tools import (
    LinkedInOpenTool,
    LinkedInReadFeedTool,
    LinkedInPreparePostTool,
    LinkedInPrepareCommentTool,
    LinkedInPublishPostTool,
)
from tools.integrations.content_tools import ContentGenerateLinkedInPostTool


@pytest.mark.asyncio
async def test_content_agent_linkedin_draft_generation():
    """Verify ContentAgent produces a high-impact LinkedIn post draft from project metadata."""
    agent = ContentAgent()
    meta = ProjectMetadata(
        name="Heart Disease Prediction System",
        path="C:/Projects/HeartDisease",
        git_remote="https://github.com/user/heart-disease-ml",
        demo_url="https://heart-ml.demo.app",
        frameworks=["Python", "Scikit-Learn", "FastAPI"],
        key_features=["92% Classification Accuracy", "Real-time risk scoring API", "Full clinical feature set"],
        readme_summary="Machine learning pipeline for predictive cardiovascular diagnostics."
    )
    draft = agent.generate_linkedin_post(meta, tone="professional")
    
    assert draft["status"] == "DRAFT"
    assert draft["requires_confirmation"] is True
    assert "Heart Disease Prediction System" in draft["content"]
    assert "#SoftwareEngineering" in draft["content"]
    assert draft["character_count"] > 100


@pytest.mark.asyncio
async def test_linkedin_post_lifecycle_draft_then_publish():
    """Verify strict separation: prepare_post creates DRAFT, publish_post publishes."""
    service = LinkedInService()
    
    # 1. Prepare post (strictly DRAFT)
    draft_res = await service.prepare_post("🚀 Testing automated post preparation with SHIVANI.")
    assert draft_res["status"] == "DRAFT"
    assert draft_res["requires_human_approval"] is True
    draft_id = draft_res["draft_id"]
    assert draft_id.startswith("li_post_")
    
    # 2. Cannot publish invalid draft ID
    bad_pub = await service.publish_post("invalid_draft_id")
    assert bad_pub["status"] == "failed"
    
    # 3. Publish valid draft ID
    pub_res = await service.publish_post(draft_id)
    assert pub_res["status"] == "PUBLISHED"
    assert pub_res["verified"] is True
    assert pub_res["draft_id"] == draft_id


@pytest.mark.asyncio
async def test_linkedin_registered_tools():
    """Verify all registered LinkedIn tools execute and verify cleanly."""
    service = LinkedInService()
    
    open_tool = LinkedInOpenTool(linkedin_service=service)
    feed_tool = LinkedInReadFeedTool(linkedin_service=service)
    prep_post_tool = LinkedInPreparePostTool(linkedin_service=service)
    prep_comment_tool = LinkedInPrepareCommentTool(linkedin_service=service)
    pub_tool = LinkedInPublishPostTool(linkedin_service=service)
    
    # 1. Open
    o_res = await open_tool.run()
    assert (await open_tool.verify(o_res))["verified"] is True
    
    # 2. Read Feed
    f_res = await feed_tool.run()
    assert (await feed_tool.verify(f_res))["verified"] is True
    
    # 3. Prepare Post
    p_res = await prep_post_tool.run(post_text="New AI Project Showcase!")
    assert (await prep_post_tool.verify(p_res))["verified"] is True
    assert p_res["status"] == "DRAFT"
    
    # 4. Prepare Comment
    c_res = await prep_comment_tool.run(post_context="AI Discussion", comment_text="Great point!")
    assert (await prep_comment_tool.verify(c_res))["verified"] is True
    
    # 5. Publish Post
    draft_id = p_res["draft_id"]
    pub_res = await pub_tool.run(draft_id=draft_id)
    assert (await pub_tool.verify(pub_res))["verified"] is True
    assert pub_res["status"] == "PUBLISHED"
