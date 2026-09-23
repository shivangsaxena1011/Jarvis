"""
SHIVANI Tool System Base
Defines the interface, verification contracts, and metadata for all agent tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
from security.permissions.engine import RiskLevel


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
    args_schema: Optional[Type[BaseModel]] = None

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Executes the specific tool operation."""
        pass

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Verifies whether the tool action succeeded in the physical/virtual environment.
        Tools should override this with concrete checks (e.g. process running, file exists).
        """
        return {"verified": True, "note": "Default verification passed"}

    def get_metadata(self) -> Dict[str, Any]:
        schema = {}
        if self.args_schema:
            schema = self.args_schema.model_json_schema()
        return {
            "name": self.name,
            "description": self.description,
            "permission_level": self.permission_level.value,
            "timeout": self.timeout,
            "retry_policy": self.retry_policy,
            "parameters": schema
        }
