"""
SHIVANI Tool System Base
Defines the Tool interface, verification contracts, and metadata for all agent tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
from security.permissions.engine import RiskLevel
from core.errors import ValidationError, ToolError


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    verification: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0


class BaseTool(ABC):
    """Abstract base class for all SHIVANI tools."""

    name: str
    description: str
    permission_level: RiskLevel = RiskLevel.SAFE
    timeout: float = 30.0
    retry_policy: int = 1
    requires_confirmation: bool = False
    args_schema: Optional[Type[BaseModel]] = None
    output_schema: Optional[Type[BaseModel]] = None

    @property
    def risk_level(self) -> RiskLevel:
        return self.permission_level

    def validate_input(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validates arguments against args_schema."""
        if not self.args_schema:
            return arguments
        try:
            validated = self.args_schema(**arguments)
            return validated.model_dump()
        except Exception as e:
            raise ValidationError(f"Invalid parameters for tool '{self.name}': {e}")

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Executes the specific tool operation."""
        pass

    async def execute(self, **kwargs: Any) -> Any:
        """Standard execution alias."""
        return await self.run(**kwargs)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Verifies whether the tool action succeeded in the physical/virtual environment.
        Tools should override this with concrete checks (e.g. process running, file exists).
        """
        return {"verified": True, "note": "Default verification passed"}

    async def rollback_if_possible(self, **kwargs: Any) -> bool:
        """Attempt rollback if the tool supports undoing side effects."""
        return False

    def get_metadata(self) -> Dict[str, Any]:
        schema = {}
        if self.args_schema:
            schema = self.args_schema.model_json_schema()
        out_schema = {}
        if self.output_schema:
            out_schema = self.output_schema.model_json_schema()

        return {
            "name": self.name,
            "description": self.description,
            "risk_level": self.permission_level.value,
            "permission_level": self.permission_level.value,
            "timeout": self.timeout,
            "retry_policy": self.retry_policy,
            "requires_confirmation": self.requires_confirmation,
            "parameters": schema,
            "output_schema": out_schema
        }


# Standard alias
Tool = BaseTool
