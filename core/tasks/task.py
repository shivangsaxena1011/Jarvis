"""
SHIVANI Task Model & Lifecycle Management
Structured Pydantic model representing user tasks, multi-step plans, and results.
"""

from enum import Enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    WAITING_FOR_PERMISSION = "WAITING_FOR_PERMISSION"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PlanStep(BaseModel):
    id: str
    tool: str
    action: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    expected_outcome: str = ""
    status: str = "PENDING"


class TaskPlan(BaseModel):
    goal: str
    rationale: str = ""
    steps: List[PlanStep] = Field(default_factory=list)


class StepExecutionResult(BaseModel):
    step_id: str
    tool: str
    action: str
    arguments: Dict[str, Any]
    success: bool
    data: Any = None
    verification: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_request: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    plan: Optional[TaskPlan] = None
    current_step: int = 0
    step_results: List[StepExecutionResult] = Field(default_factory=list)
    
    result: Optional[str] = None
    error: Optional[str] = None
    requires_confirmation: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def user_query(self) -> str:
        """Alias for backward compatibility."""
        return self.user_request

    @property
    def state(self) -> TaskStatus:
        """Alias for backward compatibility."""
        return self.status

    @state.setter
    def state(self, value: TaskStatus) -> None:
        self.status = value

    @property
    def final_output(self) -> Optional[str]:
        """Alias for backward compatibility."""
        return self.result

    @final_output.setter
    def final_output(self, value: Optional[str]) -> None:
        self.result = value

    @property
    def current_step_index(self) -> int:
        return self.current_step

    @current_step_index.setter
    def current_step_index(self, value: int) -> None:
        self.current_step = value

    def transition_to(self, new_status: TaskStatus, message: str = "", details: Optional[Dict[str, Any]] = None) -> None:
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc).isoformat()
        if details:
            self.metadata.update(details)
        if message:
            self.metadata["last_message"] = message
