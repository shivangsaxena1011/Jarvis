"""
SHIVANI Skill Permission Manager
Evaluates requested permissions, computes permission diffs on updates,
and maps granular permissions to system RiskLevels.
"""

from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from security.permissions.engine import PermissionEngine
from security.permissions.models import RiskLevel
from skills.manifest import SkillManifest


class PermissionDiff(BaseModel):
    skill_name: str
    old_version: str
    new_version: str
    added_permissions: List[str] = Field(default_factory=list)
    removed_permissions: List[str] = Field(default_factory=list)
    unchanged_permissions: List[str] = Field(default_factory=list)
    has_escalation: bool = False
    new_risk_level: RiskLevel = RiskLevel.SAFE


class SkillPermissionManager:
    """Manages skill permission evaluation and escalation detection."""

    # Baseline mapping from permission prefixes to default RiskLevels
    DEFAULT_PERMISSION_RISKS: Dict[str, RiskLevel] = {
        "filesystem.read": RiskLevel.SAFE,
        "filesystem.write": RiskLevel.HIGH_RISK,
        "filesystem.delete": RiskLevel.CRITICAL,
        "terminal.execute": RiskLevel.CRITICAL,
        "desktop.input": RiskLevel.SENSITIVE,
        "desktop.app_control": RiskLevel.SAFE,
        "browser.navigate": RiskLevel.SAFE,
        "browser.extract": RiskLevel.SAFE,
        "browser.download": RiskLevel.SENSITIVE,
        "email.read": RiskLevel.SAFE,
        "email.send": RiskLevel.SENSITIVE,
        "github.read": RiskLevel.SAFE,
        "github.write": RiskLevel.SENSITIVE,
        "github.issues.create": RiskLevel.SAFE,
        "github.pr.create": RiskLevel.SENSITIVE,
        "social.read": RiskLevel.SAFE,
        "social.post": RiskLevel.SENSITIVE,
        "phone.control": RiskLevel.SENSITIVE,
        "phone.read_media": RiskLevel.SENSITIVE,
        "system.security": RiskLevel.CRITICAL,
    }

    def __init__(self, permission_engine: Optional[PermissionEngine] = None):
        self.engine = permission_engine or PermissionEngine()

    @classmethod
    def get_permission_risk(cls, permission_str: str) -> RiskLevel:
        """Resolves risk level for a granular permission string."""
        if permission_str in cls.DEFAULT_PERMISSION_RISKS:
            return cls.DEFAULT_PERMISSION_RISKS[permission_str]

        # Check by prefix (e.g. 'github.' or 'filesystem.')
        prefix = permission_str.split(".")[0]
        if "delete" in permission_str or "destroy" in permission_str or "kill" in permission_str:
            return RiskLevel.CRITICAL
        elif "write" in permission_str or "create" in permission_str or "send" in permission_str or "post" in permission_str:
            return RiskLevel.SENSITIVE
        elif "read" in permission_str or "search" in permission_str or "list" in permission_str:
            return RiskLevel.SAFE

        return RiskLevel.LOW_RISK

    @classmethod
    def calculate_skill_overall_risk(cls, permissions: List[str]) -> RiskLevel:
        """Determines highest risk tier requested by a list of permissions."""
        highest = RiskLevel.SAFE
        priority = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW_RISK: 1,
            RiskLevel.SENSITIVE: 2,
            RiskLevel.HIGH_RISK: 3,
            RiskLevel.CRITICAL: 4,
        }

        for p in permissions:
            r = cls.get_permission_risk(p)
            if priority[r] > priority[highest]:
                highest = r

        return highest

    @classmethod
    def diff_permissions(
        cls,
        old_manifest: SkillManifest,
        new_manifest: SkillManifest,
    ) -> PermissionDiff:
        """Compares permissions between two manifest versions."""
        old_set = set(old_manifest.permissions)
        new_set = set(new_manifest.permissions)

        added = sorted(list(new_set - old_set))
        removed = sorted(list(old_set - new_set))
        unchanged = sorted(list(old_set & new_set))

        # Check if added permissions represent an escalation (any sensitive or higher)
        new_overall = cls.calculate_skill_overall_risk(list(new_set))
        has_escalation = len(added) > 0

        return PermissionDiff(
            skill_name=new_manifest.name,
            old_version=old_manifest.version,
            new_version=new_manifest.version,
            added_permissions=added,
            removed_permissions=removed,
            unchanged_permissions=unchanged,
            has_escalation=has_escalation,
            new_risk_level=new_overall,
        )
