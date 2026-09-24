"""
SHIVANI Workflow Models
Data contracts for composable multi-agent cross-application workflows, steps, and results.
"""

from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from security.permissions.engine import RiskLevel


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str
    agent: str = Field(description="Agent responsible: 'computer', 'browser', 'content', 'github', 'system'")
    tool: str = Field(description="Registered tool name (e.g. 'project.find', 'content.linkedin_post', 'linkedin.publish')")
    input: Dict[str, Any] = Field(default_factory=dict, description="Input parameters (may contain dynamic template expressions)")
    expected_output: str = ""
    verification: Dict[str, Any] = Field(default_factory=dict)
    permission: RiskLevel = RiskLevel.SAFE
    requires_approval: bool = False
    stage: Optional[str] = None
    status: str = "PENDING"
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class WorkflowResult(BaseModel):
    workflow_id: str
    workflow_name: str
    success: bool
    status: WorkflowStatus
    current_step: int
    total_steps: int
    step_results: List[Dict[str, Any]] = Field(default_factory=list)
    final_data: Dict[str, Any] = Field(default_factory=dict)
    pending_approval_id: Optional[str] = None
    completed_stages: List[str] = Field(default_factory=list)
    checkpoints: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    message: str = ""


class Workflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    steps: List[WorkflowStep] = Field(default_factory=list)
    current_step_index: int = 0
    status: WorkflowStatus = WorkflowStatus.PENDING
    context_data: Dict[str, Any] = Field(default_factory=dict)
    pending_approval_id: Optional[str] = None
    completed_stages: List[str] = Field(default_factory=list)
    checkpoints: Dict[str, Any] = Field(default_factory=dict)
    failure_diagnostics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
