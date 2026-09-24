"""
SHIVANI Skill Manifest
Defines the declarative specification required for every installable Skill.
Enforces explicit permissions, declared capabilities, runtime versions, and sandboxing policies.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from security.permissions.models import RiskLevel
from skills.models import ActionSchema


class RuntimeRequirement(BaseModel):
    minimum_shivani_version: str = "0.1.0"
    maximum_shivani_version: Optional[str] = None
    python_version: str = ">=3.12"


class SkillPolicies(BaseModel):
    timeout_seconds: float = 30.0
    max_memory_mb: int = 512
    isolated_storage: bool = True
    network_allowed: bool = True


class SkillEntrypoint(BaseModel):
    module: str = "skill"
    class_name: str = "Skill"
    file: Optional[str] = None

    @property
    def entry_file(self) -> str:
        if self.file:
            return self.file
        return f"{self.module}.py" if not self.module.endswith(".py") else self.module


class SkillManifest(BaseModel):
    name: str = Field(..., description="Unique lowercase slug identifier, e.g. 'github'")
    display_name: str = Field(..., description="Human-readable title, e.g. 'GitHub'")
    version: str = Field(..., description="Semantic version string, e.g. '1.0.0'")
    author: str = Field(default="Community", description="Publisher or author identity")
    description: str = Field(..., description="Concise explanation of skill functionality")
    category: str = Field(
        default="Productivity",
        description="Category: Productivity, Development, Research, Communication, Media, Documents, System, AI",
    )
    runtime: RuntimeRequirement = Field(default_factory=RuntimeRequirement)
    capabilities: List[Union[str, ActionSchema]] = Field(
        default_factory=list,
        description="List of declared capabilities or ActionSchemas",
    )
    permissions: List[str] = Field(
        default_factory=list,
        description="Granular requested permissions, e.g. ['github.read', 'filesystem.write']",
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Dependencies on core capabilities or other skills, e.g. ['browser']",
    )
    entrypoint: SkillEntrypoint = Field(default_factory=SkillEntrypoint)
    policies: SkillPolicies = Field(default_factory=SkillPolicies)
    offline_capable: Union[bool, str] = True
    network_policy: List[str] = Field(
        default_factory=list,
        description="Allowed network domains, e.g. ['api.github.com'] or empty for local only",
    )
    filesystem_policy: List[str] = Field(
        default_factory=list,
        description="Allowed path scopes, e.g. ['workspace', 'temp'] or empty",
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.SAFE,
        description="Overall declared risk tier: SAFE, LOW_RISK, SENSITIVE, HIGH_RISK, CRITICAL",
    )
    tags: List[str] = Field(default_factory=list)
    signature: Optional[str] = Field(default=None, description="Optional cryptographic signature of package")
    package_hash: Optional[str] = Field(default=None, description="SHA-256 package hash")

    @property
    def actions(self) -> List[ActionSchema]:
        """Returns all declared action schemas."""
        res: List[ActionSchema] = []
        for cap in self.capabilities:
            if isinstance(cap, ActionSchema):
                res.append(cap)
            elif isinstance(cap, dict):
                try:
                    res.append(ActionSchema(**cap))
                except Exception:
                    pass
        return res

    @property
    def capability_names(self) -> List[str]:
        names: List[str] = []
        for cap in self.capabilities:
            if isinstance(cap, str):
                names.append(cap)
            elif isinstance(cap, ActionSchema):
                names.append(cap.name)
            elif isinstance(cap, dict):
                names.append(cap.get("name", "unknown"))
        return names

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def load_from_directory(cls, dir_path: Union[str, Path]) -> Optional["SkillManifest"]:
        """Finds and parses manifest.json or manifest.yaml in given directory."""
        p = Path(dir_path).resolve()
        for candidate in ["manifest.json", "manifest.yaml", "manifest.yml"]:
            mf = p / candidate
            if mf.exists():
                try:
                    content = mf.read_text(encoding="utf-8")
                    if candidate.endswith(".json"):
                        data = json.loads(content)
                    else:
                        try:
                            import yaml
                            data = yaml.safe_load(content)
                        except ImportError:
                            data = json.loads(content)
                    return cls(**data)
                except Exception:
                    return None
        return None
