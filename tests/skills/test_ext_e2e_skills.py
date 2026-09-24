"""
End-to-end test suite for Phase 13: Universal Skills & Extensibility.
"""

from pathlib import Path
import pytest

from core.config.app_dirs import AppDirectories
from tools.registry import ToolRegistry
from skills.generator import SkillGenerator, SkillScaffoldRequest
from skills.lifecycle import SkillLifecycleManager
from skills.registry import SkillRegistry
from skills.security_scanner import SkillSecurityScanner
from skills.validator import SkillValidator


@pytest.mark.asyncio
async def test_full_skill_extensibility_lifecycle(tmp_path: Path):
    app_dirs = AppDirectories(
        root_dir=tmp_path / "app",
        config_dir=tmp_path / "app" / "config",
        data_dir=tmp_path / "app" / "data",
        logs_dir=tmp_path / "app" / "logs",
        memory_dir=tmp_path / "app" / "memory",
        tasks_dir=tmp_path / "app" / "tasks",
        cache_dir=tmp_path / "app" / "cache",
        backups_dir=tmp_path / "app" / "backups",
        skills_dir=tmp_path / "app" / "skills",
    )
    app_dirs.ensure_dirs()

    tool_reg = ToolRegistry()
    skill_reg = SkillRegistry(tool_registry=tool_reg)
    lifecycle = SkillLifecycleManager(registry=skill_reg, app_dirs=app_dirs)

    # 1. Scaffold skill
    req = SkillScaffoldRequest(
        name="notes_sync",
        display_name="Notes Synchronizer",
        description="Syncs markdown notes with external cloud vault",
        category="productivity",
        actions=[{"name": "sync_notes", "description": "Syncs notes"}],
        permissions=["filesystem.read", "filesystem.write"],
    )
    pkg_dir = SkillGenerator.generate_skill(req, tmp_path / "workspace")

    # 2. Validate
    val = SkillValidator.validate_package(pkg_dir)
    assert val.is_valid is True

    # 3. Security Scan
    scan = SkillSecurityScanner().scan_directory(pkg_dir)
    assert scan.is_safe is True

    # 4. Install with user confirmation
    inst_res = await lifecycle.install(pkg_dir, user_confirmed=True)
    assert inst_res.is_ok is True
    manifest = inst_res.unwrap()
    assert manifest.name == "notes_sync"

    # 5. Enable skill
    enable_res = await lifecycle.enable("notes_sync")
    assert enable_res.is_ok is True
    active_skill = enable_res.unwrap()
    assert active_skill.name == "notes_sync"

    # 6. Verify tool auto-mounted into ToolRegistry
    tool = tool_reg.get_tool("notes_sync_action")
    assert tool is not None
    assert tool.name == "notes_sync_action"

    # 7. Execute tool via ToolRegistry
    exec_res = await tool_reg.execute_tool("notes_sync_action", {"folder": "/notes"})
    assert exec_res.success is True
    assert "Action executed successfully" in str(exec_res.data)

    # 8. Disable skill
    dis_res = await lifecycle.disable("notes_sync")
    assert dis_res.is_ok is True

    # 9. Verify tool unmounted
    assert tool_reg.get_tool("notes_sync_action") is None

    # 10. Uninstall
    uninst_res = await lifecycle.uninstall("notes_sync", purge_data=True)
    assert uninst_res.is_ok is True
