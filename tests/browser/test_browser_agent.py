"""
SHIVANI Universal Browser Agent Tests
Comprehensive test suite testing Playwright browser management, DOM observation,
natural language element resolution, action execution, multi-tab lifecycle,
content extraction, YouTube workflow, integrations, and orchestrator task flow.
"""

import os
import asyncio
import pytest
from pathlib import Path

from core.config import Settings
from core.orchestrator.orchestrator import Orchestrator
from core.tasks.task import TaskStatus
from agents.browser.agent import BrowserAgent
from agents.browser.manager import BrowserManager
from agents.browser.session import BrowserSession
from agents.browser.profile import BrowserProfileManager
from integrations.linkedin.linkedin_helper import LinkedInHelper
from integrations.gmail.gmail_helper import GmailHelper
from tests.browser.mock_server import MockTestServer
from tools.browser.navigation_tools import BrowserOpenTool, BrowserGetTitleTool
from tools.browser.interaction_tools import BrowserTypeTool, BrowserClickTool
from tools.browser.content_tools import BrowserExtractTextTool, BrowserSummarizeTool


@pytest.fixture
async def mock_server():
    server = MockTestServer()
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
async def browser_agent(tmp_path):
    prof_dir = tmp_path / "browser_profile"
    down_dir = tmp_path / "downloads"
    prof_mgr = BrowserProfileManager(base_profile_dir=str(prof_dir))
    session = BrowserSession()
    manager = BrowserManager(
        headless=True,
        profile_manager=prof_mgr,
        session=session,
        download_dir=down_dir
    )
    agent = BrowserAgent(manager=manager, profile_manager=prof_mgr, session=session)
    yield agent
    await agent.close()



@pytest.mark.asyncio
async def test_browser_navigation_and_observation(mock_server, browser_agent):
    res = await browser_agent.navigate(mock_server.base_url)
    assert res["status"] == "success"
    assert "SHIVANI Test Application" in res["title"]

    obs = await browser_agent.observe_page()
    assert obs.title == "SHIVANI Test Application"
    assert any("SHIVANI Test Portal" in h for h in obs.headings)
    assert any(e.element_type == "button" and "Search Now" in e.text for e in obs.elements)
    assert any(e.element_type == "input" and (e.element_id == "query-input" or "query-input" in (e.selector or "")) for e in obs.elements)
    assert any(e.element_type == "link" and "/target" in (e.href or "") for e in obs.elements)




@pytest.mark.asyncio
async def test_element_resolution_and_interaction(mock_server, browser_agent):
    await browser_agent.navigate(mock_server.base_url)

    # 1. Type in search input using natural language description
    type_res = await browser_agent.type_text("Search query here...", "Artificial Intelligence")
    assert type_res["status"] == "success"
    assert type_res["characters_typed"] == len("Artificial Intelligence")

    # 2. Click search button
    click_res = await browser_agent.click_element("Search Now")
    assert click_res["status"] == "success"

    # 3. Verify page state changed
    page = await browser_agent.get_active_page()
    status_text = await page.inner_text("#search-status")
    assert "Results found for: Artificial Intelligence" in status_text

    # 4. Clear input
    clear_res = await browser_agent.clear_input("Search query here...")
    assert clear_res["status"] == "success"

    # 5. Dropdown select
    select_res = await browser_agent.select_option("#country", "India")
    assert select_res["status"] == "success"
    val = await page.input_value("#country")
    assert val == "in"


@pytest.mark.asyncio
async def test_multi_tab_operations(mock_server, browser_agent):
    # Tab 1: base_url
    await browser_agent.navigate(mock_server.base_url)
    tabs_1 = await browser_agent.list_tabs()
    assert len(tabs_1) >= 1

    # Tab 2: new tab navigating to /target
    page2 = await browser_agent.new_tab(f"{mock_server.base_url}/target")
    assert "Target Destination" in await page2.title()

    tabs_2 = await browser_agent.list_tabs()
    assert len(tabs_2) == 2

    # Switch back to first tab
    first_tab_id = tabs_2[0]["id"]
    switched_page = await browser_agent.switch_tab(first_tab_id)
    assert switched_page is not None

    # Close second tab
    second_tab_id = tabs_2[1]["id"]
    closed = await browser_agent.close_tab(second_tab_id)
    assert closed is True
    assert len(await browser_agent.list_tabs()) == 1


@pytest.mark.asyncio
async def test_content_extraction_and_summarization(mock_server, browser_agent):
    await browser_agent.navigate(mock_server.base_url)

    # Text extraction
    content_text = await browser_agent.extract_text("#content-section")
    assert "Artificial Intelligence computer agents" in content_text

    # Link extraction
    links = await browser_agent.extract_links()
    assert len(links) >= 2
    assert any("Target Page" in l["text"] for l in links)

    # Summarization workflow
    summary_res = await browser_agent.summarize_page()
    assert summary_res["status"] == "success"
    assert "summary" in summary_res
    assert len(summary_res["headings"]) > 0


@pytest.mark.asyncio
async def test_file_upload_and_download(mock_server, browser_agent, tmp_path):
    await browser_agent.navigate(mock_server.base_url)

    # File upload
    dummy_file = tmp_path / "test_doc.txt"
    dummy_file.write_text("Hello SHIVANI upload verification", encoding="utf-8")
    up_res = await browser_agent.upload_file("#file-upload", str(dummy_file))
    assert up_res["status"] == "success"

    # File download
    dest_dir = tmp_path / "saved_downloads"
    down_res = await browser_agent.download_file("#download-link", destination_dir=dest_dir)
    assert down_res["status"] == "success"
    assert "sample.txt" in down_res["suggested_filename"]
    saved_file = Path(down_res["destination_path"])
    assert saved_file.exists()
    assert "Sample download content" in saved_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_youtube_workflow_disambiguation(mock_server, browser_agent):
    page = await browser_agent.get_active_page()
    # Direct to mock youtube page
    await page.goto(f"{mock_server.base_url}/youtube")

    # Trigger workflow disambiguation
    wf = browser_agent.youtube
    # The workflow searches, disambiguates best matching result, and clicks it
    # We simulate video clicking by targeting the candidate directly
    candidates = await wf._extract_video_candidates(page)
    assert len(candidates) == 2
    
    best = wf._select_best_candidate(candidates, "Arijit Singh Tum Hi Ho")
    assert best is not None
    assert "Tum Hi Ho" in best["title"]

    # Navigate to mock watch page and verify playback
    await page.goto(f"{mock_server.base_url}/watch")
    v_status = await browser_agent.verifier.verify_playback_state(page)
    assert v_status["verified"] is True
    assert v_status["playback_active"] is True


@pytest.mark.asyncio
async def test_registered_browser_tools(mock_server, browser_agent):
    open_tool = BrowserOpenTool(browser_agent=browser_agent)
    title_tool = BrowserGetTitleTool(browser_agent=browser_agent)
    type_tool = BrowserTypeTool(browser_agent=browser_agent)
    click_tool = BrowserClickTool(browser_agent=browser_agent)
    extract_tool = BrowserExtractTextTool(browser_agent=browser_agent)
    summarize_tool = BrowserSummarizeTool(browser_agent=browser_agent)

    # Open tool
    res_open = await open_tool.run(url=mock_server.base_url)
    v_open = await open_tool.verify(res_open, url=mock_server.base_url)
    assert v_open["verified"] is True

    # Title tool
    res_title = await title_tool.run()
    assert "SHIVANI Test Application" in res_title["title"]

    # Type tool
    res_type = await type_tool.run(target="Search query here...", text="Machine Learning")
    assert res_type["status"] == "success"

    # Click tool
    res_click = await click_tool.run(target="Search Now")
    assert res_click["status"] == "success"

    # Extract text tool
    res_extract = await extract_tool.run(selector="#search-status")
    assert "Machine Learning" in res_extract["text"]

    # Summarize tool
    res_sum = await summarize_tool.run()
    assert bool(res_sum.get("summary"))


@pytest.mark.asyncio
async def test_third_party_helpers(browser_agent):
    linkedin = LinkedInHelper(browser_agent)
    draft_res = await linkedin.prepare_draft("Excited to announce SHIVANI Phase 4!")
    assert draft_res["status"] in ("requires_auth", "draft_prepared")
    if draft_res["status"] == "draft_prepared":
        assert draft_res["requires_confirmation"] is True
        assert draft_res["permission_level"] == "CRITICAL"
    else:
        assert draft_res["ready_to_publish"] is False


    gmail = GmailHelper(browser_agent)
    inbox_res = await gmail.inspect_inbox()
    assert "status" in inbox_res


from core.providers.mock import MockProvider
from core.tasks.task import TaskPlan, PlanStep


@pytest.mark.asyncio
async def test_orchestrator_browser_task_execution(mock_server, tmp_path):
    settings = Settings(
        LLM_PROVIDER="mock",
        SECURITY_POLICY="lenient",
        BROWSER_HEADLESS=True,
        AUDIT_LOG_PATH=str(tmp_path / "browser_audit.jsonl")
    )
    # Direct task to local mock server for deterministic offline execution
    canned = {
        "portal kholo": TaskPlan(
            goal="Open Test Portal",
            rationale="Navigate to mock server portal",
            steps=[
                PlanStep(
                    id="1",
                    tool="browser.open",
                    action="Open mock test portal",
                    arguments={"url": mock_server.base_url},
                    expected_outcome="Portal opened"
                )
            ]
        )
    }
    mock_llm = MockProvider(canned_plans=canned)
    orch = Orchestrator(settings=settings, llm_provider=mock_llm)

    # Submit task: "Shivani, portal kholo"
    task = await orch.submit_task("Shivani, portal kholo")

    timeout = 15.0
    elapsed = 0.0
    while task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED) and elapsed < timeout:
        await asyncio.sleep(0.1)
        elapsed += 0.1

    assert task.status == TaskStatus.COMPLETED
    assert len(task.step_results) >= 1
    assert task.step_results[0].success is True
    assert task.step_results[0].verification.get("verified") is True

    await orch.shutdown()

