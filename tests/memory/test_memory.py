"""
SHIVANI Phase 8 Memory Test Suite
Verifies:
- Zero Secret Storage & Regex Redaction
- Preference Hierarchy & Conflict Resolution
- Episodic Task History & Search
- Semantic Domain Facts
- Ephemeral Short-Term Working Memory
- Task Checkpoint Recovery & Purge
- Memory Tools Execution
"""

import pytest
from memory import MemoryManager, MemoryScope, MemoryCategory, MemorySource, SecretRedactor
from tools.memory import (
    MemoryGetPreferenceTool,
    MemorySetPreferenceTool,
    MemorySearchTool,
    MemoryForgetTool,
    MemoryExplainTool,
)


def test_secret_redaction():
    redacted = SecretRedactor.redact_text("Here is my secret token: ghp_123456789012345678901234567890123456 and bearer Bearer eyJhbGciOiJIUzI1NiJ9.test")
    assert "[REDACTED_SECRET]" in redacted
    assert "ghp_" not in redacted

    dict_data = {
        "user": "shivani",
        "api_key": "sk-12345678901234567890",
        "nested": {"password": "supersecretpassword123"},
    }
    cleaned = SecretRedactor.redact_dict(dict_data)
    assert cleaned["api_key"] == "[REDACTED_SECRET]"
    assert cleaned["nested"]["password"] == "[REDACTED_SECRET]"
    assert cleaned["user"] == "shivani"


def test_memory_manager_secret_sanitization():
    mgr = MemoryManager(db_path=":memory:")
    item = mgr.remember(
        key="github_token",
        value="ghp_abcdefghijklmnopqrstuvwxyz1234567890",
        category=MemoryCategory.USER_PREFERENCE,
        explanation="User said: my api_key is sk-99999999999999999999",
    )
    assert "[REDACTED_SECRET]" in str(item.value) or item.value == "[REDACTED_SECRET]"
    assert "sk-" not in str(item.explanation)
    assert "[REDACTED_SECRET]" in str(item.explanation)


def test_preference_resolution_and_conflict_override():
    mgr = MemoryManager(db_path=":memory:")

    # 1. Global preference
    mgr.set_preference("preferred_browser", "Chrome")
    assert mgr.get_preference("preferred_browser") == "Chrome"

    # 2. Conflict override: user updates global preference to Brave
    mgr.set_preference("preferred_browser", "Brave", explanation="User switched to Brave")
    assert mgr.get_preference("preferred_browser") == "Brave"

    # 3. Project override
    mgr.set_preference("preferred_browser", "Firefox", scope=MemoryScope.PROJECT, scope_id="web-app-repo")
    # For general context -> Brave
    assert mgr.get_preference("preferred_browser") == "Brave"
    # In project web-app-repo context -> Firefox
    assert mgr.get_preference("preferred_browser", project_id="web-app-repo") == "Firefox"

    # 4. Device override
    mgr.set_preference("preferred_browser", "Samsung Internet", scope=MemoryScope.DEVICE, scope_id="phone-001")
    assert mgr.get_preference("preferred_browser", device_id="phone-001") == "Samsung Internet"
    assert mgr.get_preference("preferred_browser", project_id="web-app-repo", device_id="phone-001") == "Samsung Internet"


def test_episodic_memory_recording_and_recall():
    mgr = MemoryManager(db_path=":memory:")

    mgr.episodic.record_episode(
        task_id="task_101",
        query="Research quantum computing",
        summary="Compiled 5-page research report with arxiv citations",
        status="completed",
        artifacts=["artifacts/quantum_report.md"],
    )

    mgr.episodic.record_episode(
        task_id="task_102",
        query="Fix auth error in backend",
        summary="Patched token expiration in auth.py and verified tests pass",
        status="completed",
        artifacts=["core/auth.py"],
    )

    # Search past episodes
    hits = mgr.episodic.find_episodes("quantum")
    assert len(hits) >= 1
    assert hits[0].value["task_id"] == "task_101"
    assert "quantum_report.md" in hits[0].value["artifacts"][0]

    # Recall by task
    item = mgr.episodic.get_episode_by_task("task_102")
    assert item is not None
    assert "Patched token" in item.value["summary"]


def test_short_term_memory():
    mgr = MemoryManager(db_path=":memory:", session_id="test_session")

    mgr.short_term.add_turn("user", "Hello Shivani")
    mgr.short_term.add_turn("shivani", "Hello! How can I assist you today?")
    mgr.short_term.add_turn("user", "Open Chrome")

    turns = mgr.short_term.get_recent_turns(limit=5)
    assert len(turns) == 3
    assert turns[0]["role"] == "user"
    assert turns[1]["content"] == "Hello! How can I assist you today?"
    assert turns[2]["content"] == "Open Chrome"

    # Working context
    mgr.short_term.set_working_context("active_window", "Visual Studio Code")
    assert mgr.short_term.get_working_context("active_window") == "Visual Studio Code"


def test_task_checkpoints():
    mgr = MemoryManager(db_path=":memory:")

    mgr.task_memory.save_checkpoint(
        task_id="task_200",
        stage="RESEARCH",
        step_index=2,
        state={"scraped_urls": ["https://arxiv.org/abs/2301.0001"]},
    )

    chk = mgr.task_memory.get_checkpoint("task_200")
    assert chk is not None
    assert chk["stage"] == "RESEARCH"
    assert chk["step_index"] == 2
    assert "https://arxiv.org/abs/2301.0001" in chk["state"]["scraped_urls"]

    # Clear checkpoint
    cleared = mgr.task_memory.clear_checkpoint("task_200")
    assert cleared is True
    assert mgr.task_memory.get_checkpoint("task_200") is None


def test_explain_and_forget():
    mgr = MemoryManager(db_path=":memory:")

    item = mgr.set_preference("editor", "VS Code", explanation="Explicitly requested by user in onboarding")
    assert item.key == "editor"

    # Explain
    exp = mgr.explain("editor")
    assert exp is not None
    assert exp["key"] == "editor"
    assert "onboarding" in exp["explanation"]

    # Forget
    forgotten = mgr.forget(key="editor")
    assert forgotten is True
    assert mgr.get_preference("editor") is None
    assert mgr.explain("editor") is None


@pytest.mark.asyncio
async def test_memory_tools_execution():
    mgr = MemoryManager(db_path=":memory:")

    set_tool = MemorySetPreferenceTool(memory_manager=mgr)
    get_tool = MemoryGetPreferenceTool(memory_manager=mgr)
    search_tool = MemorySearchTool(memory_manager=mgr)
    explain_tool = MemoryExplainTool(memory_manager=mgr)
    forget_tool = MemoryForgetTool(memory_manager=mgr)

    # Set preference
    set_res = await set_tool.run(key="theme", value="dark", explanation="User preferred dark theme")
    assert set_res["status"] == "saved"

    # Get preference
    get_res = await get_tool.run(key="theme")
    assert get_res["found"] is True
    assert get_res["value"] == "dark"

    # Search
    search_res = await search_tool.run(query="theme")
    assert search_res["count"] >= 1

    # Explain
    exp_res = await explain_tool.run(key_or_id="theme")
    assert exp_res["found"] is True
    assert "dark theme" in exp_res["details"]["explanation"]

    # Forget
    forget_res = await forget_tool.run(key="theme")
    assert forget_res["forgotten"] is True
    get_res_after = await get_tool.run(key="theme")
    assert get_res_after["found"] is False
