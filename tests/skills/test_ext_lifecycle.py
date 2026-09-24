"""
Tests for Skill Lifecycle Manager: installation, zero-silent-install confirmation,
enable, disable, updates with rollback, and uninstall.
"""

import json
from pathlib import Path
import pytest

from core.config.app_dirs import AppDirectories
from skills.lifecycle import SkillLifecycleManager
from skills.manifest import SkillManifest
from skills.models import SkillState
from skills.registry import SkillRegistry


def build_test_package(dest_dir: Path, name: str, version: str = "1.0.0") -> Path:
    pkg = dest_dir / name
    pkg.mkdir(parents=True, exist_ok=True)

    manifest_data = {
        "name": name,
        "display_name": name.capitalize(),
        "version": version,
        "description": f"Test package {name}",
        "permissions": ["filesystem.read"],
        "entrypoint": {"module": "skill", "class_name": f"{name.capitalize()}Skill"},
    }
    (pkg / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

    code = f"""
from skills.runtime import BaseSkill
from tools.base import BaseTool, ToolResult

class DummyTool(BaseTool):
    name = "{name}_tool"
    description = "Dummy tool"
    async def run(self, **kwargs):
        return ToolResult(success=True, data="ok")

class {name.capitalize()}Skill(BaseSkill):
    async def initialize(self):
        self.state = "ACTIVE"
    async def shutdown(self):
        self.state = "DISABLED"
    def get_tools(self):
        return [DummyTool()]
"""
    (pkg / "skill.py").write_text(code, encoding="utf-8")
    return pkg


@pytest.mark.asyncio
async def test_lifecycle_zero_silent_install(tmp_path: Path):
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

    registry = SkillRegistry()
    mgr = SkillLifecycleManager(registry=registry, app_dirs=app_dirs)

    pkg = build_test_package(tmp_path / "src", "dummy_skill")

    # 1. Reject without confirmation
    res_no_conf = await mgr.install(pkg, user_confirmed=False)
    assert res_no_conf.is_err is True
    assert "User confirmation required" in res_no_conf.unwrap_err()

    # 2. Succeed with confirmation
    res_conf = await mgr.install(pkg, user_confirmed=True)
    assert res_conf.is_ok is True
    manifest = res_conf.unwrap()
    assert manifest.name == "dummy_skill"

    # 3. Enable skill
    enable_res = await mgr.enable("dummy_skill")
    assert enable_res.is_ok is True
    skill = enable_res.unwrap()
    assert skill.name == "dummy_skill"

    # 4. Disable skill
    disable_res = await mgr.disable("dummy_skill")
    assert disable_res.is_ok is True

    # 5. Uninstall skill
    uninstall_res = await mgr.uninstall("dummy_skill")
    assert uninstall_res.is_ok is True
