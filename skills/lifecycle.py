"""
SHIVANI Skill Lifecycle Manager
Orchestrates installation, validation, security scanning, dependency verification,
enabling, disabling, updating (with rollback), and uninstallation of skills.
Enforces zero silent installation and user confirmation policies.
"""

import asyncio
import importlib.util
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.config.app_dirs import AppDirectories, get_app_dirs
from core.utils.result import Result
from security.permissions.models import RiskLevel
from skills.dependency_resolver import DependencyResolver
from skills.manifest import SkillManifest
from skills.models import SkillHealth, SkillMetadata, SkillState
from skills.permissions import PermissionDiff, SkillPermissionManager
from skills.registry import SkillRegistry
from skills.runtime import BaseSkill
from skills.sandbox import SkillSandbox
from skills.security_scanner import SkillSecurityScanner
from skills.validator import SkillValidator

logger = logging.getLogger("shivani.skills.lifecycle")


class SkillLifecycleManager:
    """Manages skill lifecycle states and filesystem deployment."""

    def __init__(
        self,
        registry: SkillRegistry,
        app_dirs: Optional[AppDirectories] = None,
        security_scanner: Optional[SkillSecurityScanner] = None,
        permission_mgr: Optional[SkillPermissionManager] = None,
    ):
        self.registry = registry
        self.app_dirs = app_dirs or get_app_dirs()
        self.app_dirs.ensure_dirs()
        self.scanner = security_scanner or SkillSecurityScanner()
        self.permission_mgr = permission_mgr or SkillPermissionManager()

    def _get_installed_manifests(self) -> Dict[str, SkillManifest]:
        """Discovers all installed manifests in the skills directory."""
        manifests: Dict[str, SkillManifest] = {}
        if not self.app_dirs.skills_dir.exists():
            return manifests

        for skill_dir in self.app_dirs.skills_dir.iterdir():
            if skill_dir.is_dir():
                m = SkillManifest.load_from_directory(skill_dir)
                if m:
                    manifests[m.name] = m
        return manifests

    async def install(
        self,
        package_path: Path,
        user_confirmed: bool = False,
    ) -> Result[SkillManifest, str]:
        """
        Installs a skill package from a directory or archive into Shivani.
        Requires explicit user confirmation prior to execution.
        """
        pkg_path = Path(package_path).resolve()
        if not pkg_path.exists():
            return Result.err(f"Package directory not found: {pkg_path}")

        # 1. Package validation
        val_result = SkillValidator.validate_package(pkg_path)
        if not val_result.is_valid:
            err_msg = "; ".join(f"{e.field}: {e.message}" for e in val_result.errors)
            return Result.err(f"Package validation failed: {err_msg}")

        manifest = SkillManifest.load_from_directory(pkg_path)
        if not manifest:
            return Result.err("Could not load skill manifest from package.")

        # 2. Security scan
        scan_result = self.scanner.scan_directory(pkg_path)
        if not scan_result.is_safe:
            violations_str = "; ".join(f"[{v.rule_id}] {v.message}" for v in scan_result.violations)
            logger.error(f"Installation of '{manifest.name}' rejected: Security scan failed. {violations_str}")
            return Result.err(f"Security scan rejected package: {violations_str}")

        # 3. Dependency resolution
        installed = self._get_installed_manifests()
        installed[manifest.name] = manifest
        resolver = DependencyResolver(installed)
        dep_res = resolver.resolve()
        if not dep_res.is_valid:
            missing_str = ", ".join(dep_res.missing_dependencies)
            cycles_str = ", ".join(dep_res.cyclic_dependencies)
            return Result.err(f"Dependency check failed. Missing: [{missing_str}], Cycles: [{cycles_str}]")

        # 4. Permission & Risk calculation
        overall_risk = self.permission_mgr.calculate_skill_overall_risk(manifest.permissions)

        # 5. Zero silent install policy: User confirmation check
        if not user_confirmed:
            req_perms = ", ".join(manifest.permissions) or "None"
            return Result.err(
                f"User confirmation required: Skill '{manifest.name}' (v{manifest.version}) "
                f"requests permissions [{req_perms}] at risk level '{overall_risk.value}'. "
                "Pass user_confirmed=True to proceed."
            )

        # 6. Copy files to destination
        dest_dir = self.app_dirs.get_skill_dir(manifest.name)
        try:
            # Copy all files from pkg_path into dest_dir, avoiding recursive self-copies
            for item in pkg_path.iterdir():
                target = dest_dir / item.name
                if item.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)

            logger.info(f"Skill '{manifest.name}' files installed to {dest_dir}")
            return Result.ok(manifest)
        except Exception as e:
            logger.exception(f"Failed to copy skill package files: {e}")
            return Result.err(f"Failed to copy skill files: {e}")

    async def enable(self, skill_name: str) -> Result[BaseSkill, str]:
        """Loads and activates an installed skill into runtime."""
        # Check if already active
        existing = self.registry.get_skill(skill_name)
        if existing and existing.state == SkillState.ACTIVE:
            return Result.ok(existing)

        dest_dir = self.app_dirs.get_skill_dir(skill_name)
        manifest = SkillManifest.load_from_directory(dest_dir)
        if not manifest:
            return Result.err(f"Skill '{skill_name}' is not installed or manifest missing.")

        entry_file = dest_dir / manifest.entrypoint.entry_file
        if not entry_file.exists():
            return Result.err(f"Skill entrypoint file '{manifest.entrypoint.entry_file}' not found in {dest_dir}")

        try:
            # Dynamic import of entrypoint
            module_name = f"shivani_skill_{skill_name.replace('-', '_')}"
            spec = importlib.util.spec_from_file_location(module_name, entry_file)
            if not spec or not spec.loader:
                return Result.err(f"Could not build module spec for {entry_file}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            skill_class = getattr(module, manifest.entrypoint.class_name, None)
            if not skill_class:
                return Result.err(
                    f"Class '{manifest.entrypoint.class_name}' not found in module '{manifest.entrypoint.file}'"
                )

            # Build sandbox with declared policies
            sandbox = SkillSandbox(
                manifest=manifest,
                allowed_paths=[dest_dir],
            )
            # Instantiate skill
            skill_instance: BaseSkill = skill_class(manifest=manifest, sandbox=sandbox)

            # Initialize
            await skill_instance.initialize()

            # Register
            self.registry.register_skill(skill_instance)
            return Result.ok(skill_instance)

        except Exception as e:
            logger.exception(f"Failed to enable skill '{skill_name}': {e}")
            return Result.err(f"Skill activation failed: {e}")

    async def disable(self, skill_name: str) -> Result[bool, str]:
        """Gracefully shuts down and unregisters an active skill."""
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return Result.err(f"Skill '{skill_name}' is not currently active.")

        try:
            await skill.shutdown()
        except Exception as e:
            logger.warning(f"Error during skill '{skill_name}' shutdown: {e}")

        unregistered = self.registry.unregister_skill(skill_name)
        return Result.ok(unregistered)

    async def update(
        self,
        skill_name: str,
        new_package_path: Path,
        user_confirmed: bool = False,
    ) -> Result[SkillManifest, str]:
        """
        Updates an existing skill with rollback safety and escalation detection.
        """
        new_pkg = Path(new_package_path).resolve()
        current_dir = self.app_dirs.get_skill_dir(skill_name)
        old_manifest = SkillManifest.load_from_directory(current_dir)
        if not old_manifest:
            return Result.err(f"Skill '{skill_name}' is not currently installed.")

        new_manifest = SkillManifest.load_from_directory(new_pkg)
        if not new_manifest:
            return Result.err("Could not load manifest from new package.")

        # Compute diff and check for permission escalation
        diff = self.permission_mgr.diff_permissions(old_manifest, new_manifest)
        if diff.has_escalation and not user_confirmed:
            added_str = ", ".join(diff.added_permissions)
            return Result.err(
                f"Permission escalation detected during update of '{skill_name}': "
                f"New permissions requested: [{added_str}]. Pass user_confirmed=True to approve update."
            )

        # Backup current version to backups_dir
        backup_dir = self.app_dirs.backups_dir / f"{skill_name}_backup_{old_manifest.version}"
        try:
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(current_dir, backup_dir)
        except Exception as e:
            return Result.err(f"Failed to create backup before update: {e}")

        # Disable current active skill if running
        is_active = self.registry.get_skill(skill_name) is not None
        if is_active:
            await self.disable(skill_name)

        # Overwrite with new files
        try:
            for item in new_pkg.iterdir():
                target = current_dir / item.name
                if item.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)

            # Try re-enabling if was active
            if is_active:
                enable_res = await self.enable(skill_name)
                if enable_res.is_err:
                    # Rollback on activation failure!
                    logger.error(f"Updated skill failed to activate ({enable_res.unwrap_err()}). Rolling back...")
                    await self._rollback_from_dir(skill_name, backup_dir)
                    if is_active:
                        await self.enable(skill_name)
                    return Result.err(f"Update failed during activation; rolled back: {enable_res.unwrap_err()}")

            logger.info(f"Skill '{skill_name}' successfully updated to v{new_manifest.version}")
            return Result.ok(new_manifest)

        except Exception as e:
            logger.exception(f"Unexpected error updating skill '{skill_name}'. Rolling back...")
            await self._rollback_from_dir(skill_name, backup_dir)
            return Result.err(f"Update failed, rolled back: {e}")

    async def _rollback_from_dir(self, skill_name: str, backup_dir: Path) -> None:
        target_dir = self.app_dirs.get_skill_dir(skill_name)
        if backup_dir.exists():
            shutil.rmtree(target_dir)
            shutil.copytree(backup_dir, target_dir)

    async def uninstall(self, skill_name: str, purge_data: bool = False) -> Result[bool, str]:
        """Disables and removes a skill and its files."""
        # Disable if active
        if self.registry.get_skill(skill_name):
            await self.disable(skill_name)

        skill_dir = self.app_dirs.skills_dir / skill_name
        if not skill_dir.exists():
            return Result.err(f"Skill '{skill_name}' directory not found.")

        try:
            if purge_data:
                shutil.rmtree(skill_dir)
            else:
                # Remove code files and manifest, keep data / config / logs
                for item in skill_dir.iterdir():
                    if item.name not in ["data", "logs", "config"]:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
            logger.info(f"Skill '{skill_name}' successfully uninstalled.")
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to uninstall skill '{skill_name}': {e}")
