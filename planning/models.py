"""
SHIVANI Planning Models — Structured Goals, Subtasks, Graph Nodes, and Enums.
"""

from __future__ import annotations
from enum import Enum
import uuid
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field

from security.permissions.engine import RiskLevel


class ExecutionStrategy(str, Enum):
    """Execution strategy applied to a task plan."""
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"
    HIERARCHICAL = "HIERARCHICAL"
    OPPORTUNISTIC_RECOVERY = "OPPORTUNISTIC_RECOVERY"
    DRY_RUN = "DRY_RUN"


class SubTaskStatus(str, Enum):
    """Lifecycle status of an individual subtask."""
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    WAITING_APPROVAL = "WAITING_APPROVAL"


class Goal(BaseModel):
    """Structured representation of a high-level user goal."""
    id: str = Field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    raw_query: str
    objective: str
    scope: str = "general"
    desired_outputs: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[str] = None
    quality_requirements: List[str] = Field(default_factory=list)
    approval_requirements: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    clarification_options: List[str] = Field(default_factory=list)


class SubTaskPlan(BaseModel):
    """A concrete, executable step in an agentic workflow."""
    id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    assigned_agent: str  # e.g. 'research_agent', 'coding_agent', 'presentation_agent', 'browser_agent'
    stage: str = "EXECUTION"  # 'RESEARCH', 'ANALYSIS', 'IMPLEMENTATION', 'TESTING', 'PRESENTATION', etc.
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.SAFE
    expected_result: str = ""
    verification_method: str = "automatic"
    timeout_seconds: float = 60.0
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_retries": 2, "backoff": 1.5})
    status: SubTaskStatus = SubTaskStatus.PENDING
    result_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskNode(BaseModel):
    """Node in a directed dependency TaskGraph."""
    subtask: SubTaskPlan
    predecessors: Set[str] = Field(default_factory=set)
    successors: Set[str] = Field(default_factory=set)
    priority: int = 10  # Higher number = higher execution urgency
    critical_path: bool = False


class PlanValidationResult(BaseModel):
    """Outcome of formal plan validation."""
    is_valid: bool = True
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ReplanTrigger(BaseModel):
    """Context describing a failure requiring dynamic replanning."""
    failed_node_id: str
    failure_reason: str
    error_type: str = "EXECUTION_ERROR"  # 'TOOL_FAILURE', 'TIMEOUT', 'PERMISSION_DENIED', 'INPUT_MISSING'
    diagnosis: str = ""
    suggested_action: str = "RETRY_WITH_FALLBACK"
