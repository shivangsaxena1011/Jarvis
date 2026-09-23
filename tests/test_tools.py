"""
Unit tests for SHIVANI Tool System.
"""

import pytest
from pathlib import Path
from tools.registry import ToolRegistry
from security.permissions.engine import PermissionEngine
from security.audit.logger import AuditLogger
from tools.computer.system_tools import ScreenshotTool, GetActiveWindowTool, ListProcessesTool
from tools.filesystem.file_tools import ListDirectoryTool, ReadFileTool, WriteFileTool, SafeDeleteTool
from tools.terminal.shell_tools import TerminalExecuteTool


@pytest.fixture
def registry(tmp_path):
    perm = PermissionEngine(policy="test") # test policy allows non-blocking execution in automated unit tests
    audit = AuditLogger(log_path=str(tmp_path / "test_audit.jsonl"))

    reg = ToolRegistry(permission_engine=perm, audit_logger=audit)
    reg.register(ScreenshotTool())
    reg.register(GetActiveWindowTool())
    reg.register(ListProcessesTool())
    reg.register(ListDirectoryTool())
    reg.register(ReadFileTool())
    reg.register(WriteFileTool())
    reg.register(SafeDeleteTool())
    reg.register(TerminalExecuteTool())
    return reg


@pytest.mark.asyncio
async def test_tool_registration(registry):
    tools = registry.list_tools()
    assert len(tools) == 8
    names = [t["name"] for t in tools]
    assert "computer.screenshot" in names
    assert "filesystem.read_file" in names
    assert "terminal.execute" in names


@pytest.mark.asyncio
async def test_screenshot_tool(registry):
    res = await registry.execute_tool("computer.screenshot", {})
    assert res.success is True
    assert res.verification.get("verified") is True
    assert Path(res.data["path"]).exists()


@pytest.mark.asyncio
async def test_filesystem_lifecycle(registry, tmp_path):
    test_file = tmp_path / "shivani_test.txt"
    content = "Hello from Shivani test suite!"

    # 1. Write File
    write_res = await registry.execute_tool(
        "filesystem.write_file",
        {"path": str(test_file), "content": content}
    )
    assert write_res.success is True
    assert write_res.verification.get("verified") is True

    # 2. Read File
    read_res = await registry.execute_tool(
        "filesystem.read_file",
        {"path": str(test_file)}
    )
    assert read_res.success is True
    assert read_res.data["content"] == content

    # 3. List Directory
    list_res = await registry.execute_tool(
        "filesystem.list_dir",
        {"path": str(tmp_path)}
    )
    assert list_res.success is True
    names = [item["name"] for item in list_res.data]
    assert "shivani_test.txt" in names

    # 4. Safe Delete
    del_res = await registry.execute_tool(
        "filesystem.safe_delete",
        {"path": str(test_file)}
    )
    assert del_res.success is True
    assert del_res.verification.get("verified") is True
    assert not test_file.exists()


@pytest.mark.asyncio
async def test_terminal_execute_safe(registry):
    res = await registry.execute_tool(
        "terminal.execute",
        {"command": "echo ShivaniAgent"}
    )
    assert res.success is True
    assert "ShivaniAgent" in res.data["stdout"]
    assert res.verification.get("verified") is True


@pytest.mark.asyncio
async def test_terminal_execute_blocked_command(registry):
    res = await registry.execute_tool(
        "terminal.execute",
        {"command": "format c:"}
    )
    assert res.success is False
    assert "Security Sandbox Violation" in res.error
