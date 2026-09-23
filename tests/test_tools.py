"""
Unit tests for SHIVANI Tool System Foundation.
"""

import pytest
from pathlib import Path
from tools.registry import ToolRegistry
from security.permissions.engine import PermissionEngine
from security.audit.logger import AuditLogger
from tools.computer.system_tools import (
    ScreenshotTool,
    ActiveWindowTool,
    GetActiveWindowTool,
    ListProcessesTool,
    OpenAppTool,
    CloseAppTool,
    ListWindowsTool,
)
from tools.filesystem.file_tools import (
    ListDirectoryTool,
    LegacyListDirTool,
    SearchFilesTool,
    ReadMetadataTool,
    CreateDirectoryTool,
    ReadFileTool,
    WriteFileTool,
)
from tools.terminal.shell_tools import TerminalExecuteTool
from core.errors import PermissionDeniedError


@pytest.fixture
def registry(tmp_path):
    perm = PermissionEngine(policy="test")
    audit = AuditLogger(log_path=str(tmp_path / "test_audit.jsonl"))

    reg = ToolRegistry(permission_engine=perm, audit_logger=audit)
    reg.register(ScreenshotTool())
    reg.register(ActiveWindowTool())
    reg.register(GetActiveWindowTool())
    reg.register(ListWindowsTool())
    reg.register(ListProcessesTool())
    reg.register(OpenAppTool())
    reg.register(CloseAppTool())
    reg.register(ListDirectoryTool())
    reg.register(LegacyListDirTool())
    reg.register(SearchFilesTool())
    reg.register(ReadMetadataTool())
    reg.register(CreateDirectoryTool())
    reg.register(ReadFileTool())
    reg.register(WriteFileTool())
    reg.register(TerminalExecuteTool())
    return reg


@pytest.mark.asyncio
async def test_tool_registration(registry):
    tools = registry.list_tools()
    assert len(tools) >= 12
    names = [t["name"] for t in tools]
    assert "computer.screenshot" in names
    assert "computer.active_window" in names
    assert "computer.list_windows" in names
    assert "computer.close_app" in names
    assert "filesystem.list" in names
    assert "filesystem.search" in names
    assert "filesystem.read_metadata" in names
    assert "filesystem.create_directory" in names
    assert "terminal.execute" in names


@pytest.mark.asyncio
async def test_screenshot_tool(registry):
    res = await registry.execute_tool("computer.screenshot", {})
    assert res.success is True
    assert res.verification.get("verified") is True
    assert Path(res.data["path"]).exists()


@pytest.mark.asyncio
async def test_active_and_list_windows(registry):
    # Active window
    res_active = await registry.execute_tool("computer.active_window", {})
    assert res_active.success is True
    assert "window_title" in res_active.data

    # List windows
    res_list = await registry.execute_tool("computer.list_windows", {})
    assert res_list.success is True
    assert isinstance(res_list.data, list)


@pytest.mark.asyncio
async def test_filesystem_foundation(registry, tmp_path):
    # 1. Create Directory
    new_dir = tmp_path / "subproject"
    res_mkdir = await registry.execute_tool(
        "filesystem.create_directory",
        {"path": str(new_dir)}
    )
    assert res_mkdir.success is True
    assert new_dir.exists()

    # 2. Write File
    sample_file = new_dir / "module.py"
    res_write = await registry.execute_tool(
        "filesystem.write_file",
        {"path": str(sample_file), "content": "print('hello world')"}
    )
    assert res_write.success is True

    # 3. Read Metadata
    res_meta = await registry.execute_tool(
        "filesystem.read_metadata",
        {"path": str(sample_file)}
    )
    assert res_meta.success is True
    assert res_meta.data["is_file"] is True
    assert res_meta.data["size_bytes"] > 0

    # 4. Search Files
    res_search = await registry.execute_tool(
        "filesystem.search",
        {"path": str(tmp_path), "pattern": "*.py"}
    )
    assert res_search.success is True
    assert len(res_search.data) >= 1
    assert any(m["name"] == "module.py" for m in res_search.data)

    # 5. List Directory
    res_list = await registry.execute_tool(
        "filesystem.list",
        {"path": str(new_dir)}
    )
    assert res_list.success is True
    assert any(f["name"] == "module.py" for f in res_list.data)


@pytest.mark.asyncio
async def test_filesystem_protected_system_dir_rejection(registry):
    # Registry execution wraps in ToolResult failure
    res = await registry.execute_tool(
        "filesystem.list",
        {"path": r"C:\Windows\System32"}
    )
    assert res.success is False
    assert "Access to protected operating system directory is denied" in res.error

    # Direct run raises PermissionDeniedError
    with pytest.raises(PermissionDeniedError):
        tool = registry.get_tool("filesystem.list")
        await tool.run(path=r"C:\Windows\System32")



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
