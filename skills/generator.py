"""
SHIVANI Skill Generator
Scaffolds new skill packages with manifests, runtime classes, and boilerplate tools
from natural language descriptions or templates.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

from skills.manifest import SkillManifest, SkillEntrypoint, SkillPolicies
from skills.models import ActionSchema, ActionVerb


class SkillScaffoldRequest(BaseModel):
    name: str
    display_name: str
    description: str
    author: str = "SHIVANI Developer"
    category: str = "productivity"
    actions: List[Dict[str, str]] = []  # [{"name": "fetch_data", "description": "Fetches data"}]
    permissions: List[str] = []
    template_type: str = "api"  # "api" | "tool" | "app"


class SkillGenerator:
    """Generates standard skill directory structure and code templates."""

    @classmethod
    def generate_skill(cls, request: SkillScaffoldRequest, output_dir: Path) -> Path:
        """Creates a complete skill package ready for validation and installation."""
        target_dir = Path(output_dir) / request.name
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Prepare actions
        action_schemas: List[ActionSchema] = []
        for a in request.actions:
            action_schemas.append(
                ActionSchema(
                    name=a.get("name", "run_action"),
                    verb=ActionVerb.EXECUTE,
                    description=a.get("description", "Execute action"),
                    parameters={"type": "object", "properties": {}},
                    required_permissions=request.permissions,
                )
            )

        if not action_schemas:
            action_schemas.append(
                ActionSchema(
                    name="run",
                    verb=ActionVerb.EXECUTE,
                    description=f"Run main action for {request.name}",
                    parameters={"type": "object", "properties": {}},
                )
            )

        # 2. Build manifest
        manifest = SkillManifest(
            name=request.name,
            version="0.1.0",
            display_name=request.display_name,
            description=request.description,
            author=request.author,
            category=request.category,
            permissions=request.permissions,
            entrypoint=SkillEntrypoint(file="skill.py", class_name=f"{cls._to_camel_case(request.name)}Skill"),
            capabilities=action_schemas,
            policies=SkillPolicies(timeout_seconds=30),
        )

        manifest_file = target_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest.model_dump(), indent=2), encoding="utf-8")

        # 3. Generate skill.py
        class_name = f"{cls._to_camel_case(request.name)}Skill"
        code = cls._generate_skill_code(request, class_name)
        (target_dir / "skill.py").write_text(code, encoding="utf-8")

        # 4. Generate README.md
        readme = f"# {request.display_name}\n\n{request.description}\n\n## Actions\n"
        for act in action_schemas:
            readme += f"- `{act.name}`: {act.description}\n"
        (target_dir / "README.md").write_text(readme, encoding="utf-8")

        return target_dir

    @staticmethod
    def _to_camel_case(text: str) -> str:
        parts = text.replace("-", "_").split("_")
        return "".join(p.capitalize() for p in parts)

    @classmethod
    def _generate_skill_code(cls, request: SkillScaffoldRequest, class_name: str) -> str:
        return f'''"""
{request.display_name} - SHIVANI Skill Implementation
"""

import logging
from typing import Any, Dict, List
from skills.runtime import BaseSkill
from skills.models import SkillHealth
from tools.base import BaseTool, ToolResult
from security.permissions.models import RiskLevel


class {class_name}Tool(BaseTool):
    name = "{request.name}_action"
    description = "{request.description}"
    permission_level = RiskLevel.SAFE

    async def run(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data={{"message": "Action executed successfully", "params": kwargs}})


class {class_name}(BaseSkill):
    """Implementation of {request.display_name}."""

    async def initialize(self) -> None:
        self.logger.info("Initializing {request.display_name}")

    async def shutdown(self) -> None:
        self.logger.info("Shutting down {request.display_name}")

    def get_tools(self) -> List[BaseTool]:
        return [{class_name}Tool()]

    async def execute_action(self, action_name: str, **kwargs: Any) -> Any:
        return {{"status": "ok", "action": action_name, "details": kwargs}}
'''
