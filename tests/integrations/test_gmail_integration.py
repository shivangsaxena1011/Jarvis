"""
Unit & Integration Tests for SHIVANI Gmail Integration & Tools.
"""

import pytest
from integrations.gmail.service import GmailService
from tools.integrations.gmail_tools import (
    GmailOpenTool,
    GmailListUnreadTool,
    GmailSearchTool,
    GmailSummarizeTool,
    GmailCleanupProposalTool,
    GmailExecuteCleanupTool,
    GmailDeleteTool,
)


@pytest.fixture
def sample_test_emails():
    return [
        {"id": "msg_1", "sender": "Security Alert <no-reply@accounts.google.com>", "subject": "New sign-in from Windows Desktop", "snippet": "Your account was accessed from a new device...", "is_unread": True},
        {"id": "msg_2", "sender": "Prof. Sharma <sharma@university.edu>", "subject": "Project Review Meeting Tomorrow", "snippet": "Please bring your documentation and status report...", "is_unread": True},
        {"id": "msg_3", "sender": "TechFlash Newsletter <news@techflash.io>", "subject": "Top 10 AI Frameworks This Week", "snippet": "Discover the latest weekly AI agent architectures...", "is_unread": True},
        {"id": "msg_4", "sender": "SuperShop Deals <deals@supershop.xyz>", "subject": "Mega Sale: Up to 80% discount today!", "snippet": "Don't miss our exclusive discounts...", "is_unread": True},
    ]


@pytest.mark.asyncio
async def test_gmail_inbox_summarization(sample_test_emails):
    """Verify GmailService categorizes unread emails and generates an executive summary."""
    service = GmailService()
    summary = await service.summarize_inbox(messages=sample_test_emails)
    
    assert summary["status"] == "success"
    assert summary["total_unread"] > 0
    assert "categories" in summary
    assert "summary_text" in summary
    assert summary["summary_text"].startswith("### Executive Email Briefing")
    
    # Check that categories exist
    cats = summary["categories"]
    assert "important" in cats or "work_college" in cats or "promotional" in cats


@pytest.mark.asyncio
async def test_gmail_cleanup_two_stage_proposal(sample_test_emails):
    """Verify two-stage cleanup flow: proposal generation first, then execution with approval."""
    service = GmailService()
    
    # Stage 1: Generate Proposal
    proposal = await service.generate_cleanup_proposal(messages=sample_test_emails, max_age_days=30)
    assert proposal["status"] == "proposal_ready"
    assert proposal["requires_human_approval"] is True
    assert proposal["proposal_id"].startswith("clean_")
    assert proposal["count_identified"] > 0
    
    # Stage 2: Execute with invalid ID fails safely
    invalid_exec = await service.execute_cleanup("invalid_proposal_id")
    assert invalid_exec["status"] == "failed"
    assert "not found" in invalid_exec["error"].lower()
    
    # Stage 2: Execute with valid ID succeeds
    valid_exec = await service.execute_cleanup(proposal["proposal_id"], action="archive")
    assert valid_exec["status"] == "executed"
    assert valid_exec["action_taken"] == "archive"
    assert valid_exec["count_processed"] > 0


@pytest.mark.asyncio
async def test_gmail_registered_tools():
    """Verify all registered Gmail tools execute and verify cleanly."""
    service = GmailService()
    
    open_tool = GmailOpenTool(gmail_service=service)
    list_tool = GmailListUnreadTool(gmail_service=service)
    search_tool = GmailSearchTool(gmail_service=service)
    sum_tool = GmailSummarizeTool(gmail_service=service)
    prop_tool = GmailCleanupProposalTool(gmail_service=service)
    exec_tool = GmailExecuteCleanupTool(gmail_service=service)
    del_tool = GmailDeleteTool(gmail_service=service)
    
    # 1. Open
    o_res = await open_tool.run()
    assert (await open_tool.verify(o_res))["verified"] is True
    
    # 2. List Unread
    l_res = await list_tool.run(limit=5)
    assert (await list_tool.verify(l_res))["verified"] is True
    
    # 3. Search
    s_res = await search_tool.run(query="meeting")
    assert (await search_tool.verify(s_res))["verified"] is True
    
    # 4. Summarize
    sm_res = await sum_tool.run()
    assert (await sum_tool.verify(sm_res))["verified"] is True
    
    # 5. Cleanup Proposal
    p_res = await prop_tool.run()
    assert (await prop_tool.verify(p_res))["verified"] is True
    
    # 6. Execute Cleanup
    pid = p_res["proposal_id"]
    e_res = await exec_tool.run(proposal_id=pid, action="archive")
    assert (await exec_tool.verify(e_res))["verified"] is True
    
    # 7. Delete (CRITICAL)
    d_res = await del_tool.run(message_id="msg_999")
    assert (await del_tool.verify(d_res))["verified"] is True
