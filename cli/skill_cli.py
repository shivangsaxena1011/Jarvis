"""
SHIVANI Skill CLI Subcommand Handler
Provides CLI commands for skill discovery, validation, installation, activation,
updates with rollback, uninstallation, and scaffolding.
"""

import asyncio
from pathlib import Path
from typing import List, Optional

from core.config.app_dirs import get_app_dirs
from skills.generator import SkillGenerator, SkillScaffoldRequest
from skills.lifecycle import SkillLifecycleManager
from skills.manifest import SkillManifest
from skills.registry import SkillRegistry


def handle_skill_cli(args) -> int:
    action = getattr(args, "skill_action", None)
    if not action:
        print("Usage: shivani skill {list|info|install|enable|disable|update|uninstall|scaffold} [options]")
        return 1

    registry = SkillRegistry()
    lifecycle = SkillLifecycleManager(registry=registry)

    if action == "list":
        return _handle_list(lifecycle)
    elif action == "info":
        return _handle_info(lifecycle, args.name)
    elif action == "install":
        return asyncio.run(_handle_install(lifecycle, args.path, getattr(args, "yes", False)))
    elif action == "enable":
        return asyncio.run(_handle_enable(lifecycle, args.name))
    elif action == "disable":
        return asyncio.run(_handle_disable(lifecycle, args.name))
    elif action == "update":
        return asyncio.run(_handle_update(lifecycle, args.name, args.path, getattr(args, "yes", False)))
    elif action == "uninstall":
        return asyncio.run(_handle_uninstall(lifecycle, args.name, getattr(args, "purge_data", False)))
    elif action == "scaffold":
        return _handle_scaffold(args.name, getattr(args, "type", "api"), getattr(args, "out", "."))
    else:
        print(f"Unknown skill action: {action}")
        return 1


def _handle_list(lifecycle: SkillLifecycleManager) -> int:
    manifests = lifecycle._get_installed_manifests()
    print("=== INSTALLED SKILLS ===")
    if not manifests:
        print("  No skills installed. Use 'shivani skill install <path>' or 'scaffold' to add capabilities.")
        return 0

    for name, m in manifests.items():
        print(f"  * {m.display_name} ({m.name}) v{m.version}")
        print(f"    Category   : {m.category}")
        print(f"    Description: {m.description}")
        print(f"    Permissions: {', '.join(m.permissions) if m.permissions else 'None'}")
        print(f"    Actions    : {', '.join(m.capability_names) if m.capability_names else 'None'}")
        print()
    return 0


def _handle_info(lifecycle: SkillLifecycleManager, skill_name: str) -> int:
    manifests = lifecycle._get_installed_manifests()
    m = manifests.get(skill_name)
    if not m:
        print(f"Skill '{skill_name}' is not installed.")
        return 1

    print(f"=== SKILL INFO: {m.display_name} ({m.name}) ===")
    print(f"Version    : {m.version}")
    print(f"Author     : {m.author}")
    print(f"Category   : {m.category}")
    print(f"Description: {m.description}")
    print(f"Permissions: {', '.join(m.permissions) if m.permissions else 'None'}")
    print(f"Policies   : timeout={m.policies.timeout_seconds}s, network={m.policies.network_allowed}")
    print("Actions:")
    for a in m.actions:
        print(f"  - {a.name}: {a.description} (verb: {a.verb.value})")
    return 0


async def _handle_install(lifecycle: SkillLifecycleManager, pkg_path: str, confirmed: bool) -> int:
    p = Path(pkg_path).resolve()
    print(f"Inspecting package at {p}...")
    res = await lifecycle.install(p, user_confirmed=confirmed)
    if res.is_err:
        print(f"[REJECTED] {res.unwrap_err()}")
        if not confirmed and "User confirmation required" in res.unwrap_err():
            print("To approve installation, re-run with --yes flag.")
        return 1

    manifest = res.unwrap()
    print(f"[SUCCESS] Skill '{manifest.display_name}' (v{manifest.version}) successfully installed!")
    return 0


async def _handle_enable(lifecycle: SkillLifecycleManager, skill_name: str) -> int:
    res = await lifecycle.enable(skill_name)
    if res.is_err:
        print(f"[ERROR] Failed to enable skill '{skill_name}': {res.unwrap_err()}")
        return 1
    print(f"[SUCCESS] Skill '{skill_name}' enabled and activated into runtime.")
    return 0


async def _handle_disable(lifecycle: SkillLifecycleManager, skill_name: str) -> int:
    res = await lifecycle.disable(skill_name)
    if res.is_err:
        print(f"[ERROR] Failed to disable skill '{skill_name}': {res.unwrap_err()}")
        return 1
    print(f"[SUCCESS] Skill '{skill_name}' disabled and cleanly shut down.")
    return 0


async def _handle_update(lifecycle: SkillLifecycleManager, skill_name: str, pkg_path: str, confirmed: bool) -> int:
    p = Path(pkg_path).resolve()
    res = await lifecycle.update(skill_name, p, user_confirmed=confirmed)
    if res.is_err:
        print(f"[ERROR] Update failed: {res.unwrap_err()}")
        return 1
    m = res.unwrap()
    print(f"[SUCCESS] Skill '{skill_name}' successfully updated to v{m.version}!")
    return 0


async def _handle_uninstall(lifecycle: SkillLifecycleManager, skill_name: str, purge_data: bool) -> int:
    res = await lifecycle.uninstall(skill_name, purge_data=purge_data)
    if res.is_err:
        print(f"[ERROR] Failed to uninstall skill '{skill_name}': {res.unwrap_err()}")
        return 1
    print(f"[SUCCESS] Skill '{skill_name}' uninstalled (purge_data={purge_data}).")
    return 0


def _handle_scaffold(name: str, template_type: str, out_dir: str) -> int:
    req = SkillScaffoldRequest(
        name=name.lower().replace(" ", "_"),
        display_name=name.capitalize(),
        description=f"Automated skill for {name}",
        template_type=template_type,
    )
    target = SkillGenerator.generate_skill(req, Path(out_dir))
    print(f"[SUCCESS] Scaffolding created at: {target}")
    print(f"Files created: manifest.json, skill.py, README.md")
    return 0
