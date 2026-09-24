"""
SHIVANI Personal Productivity OS — Core Models (Phase 16).
Defines strongly-typed Pydantic V2 models for Goals, Milestones, Projects,
Tasks, Decisions, Requirements, Blockers, Focus Sessions, and Daily Plans.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# ENUMS
# ==============================================================================

class GoalStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class MilestoneStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class ProjectStatus(str, Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class TaskStatus(str, Enum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DEFERRED = "DEFERRED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class RequirementStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED = "VERIFIED"


class BlockerStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class PlanStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


# ==============================================================================
# MODELS
# ==============================================================================

class Milestone(BaseModel):
    """A significant checkpoint within a project or goal."""
    id: str = Field(default_factory=lambda: f"ms_{uuid.uuid4().hex[:8]}")
    goal_id: Optional[str] = None
    project_id: Optional[str] = None
    title: str
    description: str = ""
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED
    target_date: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    dependencies: List[str] = Field(default_factory=list)  # list of milestone IDs
    tasks: List[str] = Field(default_factory=list)  # list of task IDs
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Goal(BaseModel):
    """High-level user aspiration or strategic outcome."""
    id: str = Field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    category: str = "General"  # Learning, Projects, Career, Personal, etc.
    status: GoalStatus = GoalStatus.ACTIVE
    priority: TaskPriority = TaskPriority.MEDIUM
    target_date: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    milestones: List[str] = Field(default_factory=list)  # milestone IDs
    projects: List[str] = Field(default_factory=list)  # project IDs
    tasks: List[str] = Field(default_factory=list)  # task IDs
    metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Project(BaseModel):
    """A first-class managed project container linking code, tasks, decisions, and artifacts."""
    id: str = Field(default_factory=lambda: f"proj_{uuid.uuid4().hex[:8]}")
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    priority: TaskPriority = TaskPriority.MEDIUM
    owner: str = "User"
    codebase_path: Optional[str] = None
    repo_url: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    milestones: List[str] = Field(default_factory=list)
    tasks: List[str] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PersonalTask(BaseModel):
    """A discrete unit of work with dependencies, estimates, and project associations."""
    id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: Optional[str] = None
    goal_id: Optional[str] = None
    milestone_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)  # task IDs that must complete first
    assignee: str = "user"  # "user", "shivani", "agent:coding", etc.
    due_date: Optional[str] = None
    estimated_duration_minutes: int = 30
    actual_duration_minutes: int = 0
    tags: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    automation_id: Optional[str] = None  # optional automation to trigger upon completion
    artifacts: List[str] = Field(default_factory=list)  # file paths or artifact IDs
    notes: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class Decision(BaseModel):
    """An architectural, technical, or strategic decision recorded with provenance."""
    id: str = Field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:8]}")
    project_id: Optional[str] = None
    topic: str
    decision: str
    reason: str
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    status: DecisionStatus = DecisionStatus.ACTIVE
    superseded_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Requirement(BaseModel):
    """A tracked requirement linking design, implementation, and tests."""
    id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    project_id: Optional[str] = None
    req_id: str  # e.g. "REQ-042"
    title: str
    description: str = ""
    design: str = ""
    implementation: str = ""
    test_cases: List[str] = Field(default_factory=list)
    status: RequirementStatus = RequirementStatus.PROPOSED
    verified: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Blocker(BaseModel):
    """An issue blocking progress on a project, task, or milestone."""
    id: str = Field(default_factory=lambda: f"blk_{uuid.uuid4().hex[:8]}")
    project_id: Optional[str] = None
    title: str
    description: str = ""
    affected_tasks: List[str] = Field(default_factory=list)
    dependency: str = ""
    owner: str = "user"
    status: BlockerStatus = BlockerStatus.OPEN
    resolution: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None


class FocusSession(BaseModel):
    """A timed focus block dedicated to a specific task."""
    id: str = Field(default_factory=lambda: f"focus_{uuid.uuid4().hex[:8]}")
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    task_title: str = ""
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    target_duration_minutes: int = 60
    actual_duration_minutes: int = 0
    interruptions: int = 0
    completed: bool = False
    notes: str = ""


class TimeBlock(BaseModel):
    """A scheduled block of time in a proposed day plan."""
    start_time: str  # "09:00"
    end_time: str    # "10:30"
    task_id: Optional[str] = None
    title: str
    category: str = "Deep Work"  # Deep Work, Review, Meeting, Routine, Admin
    description: str = ""


class DailyPlan(BaseModel):
    """A proposed and user-reviewed daily schedule."""
    id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    time_blocks: List[TimeBlock] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.PROPOSED
    total_planned_minutes: int = 0
    available_minutes: int = 480  # Default 8 hours
    notes: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PriorityScore(BaseModel):
    """Structured transparent priority scoring for a task."""
    task_id: str
    total_score: float
    factors: Dict[str, float] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)
