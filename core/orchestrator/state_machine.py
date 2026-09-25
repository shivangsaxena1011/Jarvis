"""
SHIVANI Task State Machine
Tracks task lifecycle: PENDING -> PLANNING -> WAITING_FOR_PERMISSION ->
EXECUTING -> VERIFYING -> RECOVERING -> COMPLETED / FAILED / CANCELLED.
"""

from enum import Enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.llm.base import TaskPlan


class TaskState(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    WAITING_FOR_PERMISSION = "WAITING_FOR_PERMISSION"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"



class TaskEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    state: TaskState
    message: str
    details: Optional[Dict[str, Any]] = None


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
    user_query: str
    normalized_query: str = ""
    state: TaskState = TaskState.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    
    plan: Optional[TaskPlan] = None
    current_step_index: int = 0
    step_results: List[StepExecutionResult] = Field(default_factory=list)
    events: List[TaskEvent] = Field(default_factory=list)
    
    final_output: Optional[str] = None
    error: Optional[str] = None

    def transition_to(self, new_state: TaskState, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.state = new_state
        self.events.append(TaskEvent(state=new_state, message=message, details=details))
        if new_state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED):
            self.completed_at = datetime.now(timezone.utc).isoformat()
