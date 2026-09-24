"""
SHIVANI Automation Data Models & Contracts (Phase 15).
Typed, persistent, structured representations for proactive automations,
triggers, conditions, execution steps, runs, permissions, and audit history.
"""

from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from security.permissions.models import RiskLevel


class TriggerType(str, Enum):
    SCHEDULE = "schedule"
    INTERVAL = "interval"
    ONCE = "once"
    EVENT = "event"
    FILE = "file"
    DEVICE = "device"
    WEBHOOK = "webhook"


class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    CHANGED = "changed"
    MATCHES = "matches"


class LogicalOperator(str, Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class FailurePolicy(str, Enum):
    STOP = "STOP"
    RETRY = "RETRY"
    SKIP_STEP = "SKIP_STEP"
    PAUSE_FOR_USER = "PAUSE_FOR_USER"
    CONTINUE_WITH_WARNING = "CONTINUE_WITH_WARNING"


class AutomationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    DRAFT = "DRAFT"


class RunStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    TRIGGERED = "TRIGGERED"
    EVALUATING = "EVALUATING"
    WAITING_FOR_PERMISSION = "WAITING_FOR_PERMISSION"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"
    EXPIRED = "EXPIRED"


class AutomationScope(str, Enum):
    GLOBAL = "GLOBAL"
    PROJECT = "PROJECT"
    DEVICE = "DEVICE"
    ACCOUNT = "ACCOUNT"
    FOLDER = "FOLDER"
    TASK = "TASK"
    SESSION = "SESSION"


class AutomationSource(str, Enum):
    USER_CREATED = "USER_CREATED"
    TEMPLATE = "TEMPLATE"
    IMPORTED = "IMPORTED"
    SHIVANI_SUGGESTED = "SHIVANI_SUGGESTED"
    SYSTEM = "SYSTEM"


# ==============================================================================
# TRIGGER SCHEMAS
# ==============================================================================

class TimeSchedule(BaseModel):
    cron: Optional[str] = Field(default=None, description="Standard cron string, e.g. '0 8 * * 1-5' (weekdays 8 AM)")
    time_of_day: Optional[str] = Field(default=None, description="24-hour time string, e.g. '08:00'")
    days_of_week: List[str] = Field(default_factory=list, description="List of day abbreviations, e.g. ['mon', 'tue']")
    interval_seconds: Optional[int] = Field(default=None, description="Recurring interval in seconds")
    specific_datetime: Optional[str] = Field(default=None, description="ISO timestamp for one-time scheduled runs")
    timezone: str = Field(default="Asia/Kolkata", description="Target timezone, e.g. 'Asia/Kolkata', 'UTC'")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_executions: Optional[int] = None
    catch_up_policy: str = Field(default="run_latest", description="'run_latest', 'skip_if_missed', 'run_all'")


class EventFilter(BaseModel):
    event_type: str = Field(description="System EventType or custom topic (e.g. 'TASK_COMPLETED', 'device_connected')")
    topic: Optional[str] = None
    source: Optional[str] = None
    filter_expression: Dict[str, Any] = Field(default_factory=dict)


class TriggerConfig(BaseModel):
    type: TriggerType = TriggerType.SCHEDULE
    schedule: Optional[TimeSchedule] = None
    event: Optional[EventFilter] = None
    file_path: Optional[str] = None
    file_patterns: List[str] = Field(default_factory=lambda: ["*"])
    device_id: Optional[str] = None
    description: str = ""


# ==============================================================================
# CONDITION SCHEMAS (STRUCTURED PREDICATES)
# ==============================================================================

class ConditionPredicate(BaseModel):
    field: str = Field(description="Context key or dot-notated path, e.g. 'event.artifact.path' or 'unread_emails'")
    operator: ConditionOperator = ConditionOperator.EQUALS
    value: Any = None
    context: Optional[str] = None


class ConditionGroup(BaseModel):
    logical_op: LogicalOperator = LogicalOperator.AND
    predicates: List[ConditionPredicate] = Field(default_factory=list)
    nested_groups: List["ConditionGroup"] = Field(default_factory=list)


# Resolve self-referencing model
ConditionGroup.model_rebuild()


# ==============================================================================
# STEP & WORKFLOW SCHEMAS
# ==============================================================================

class AutomationStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    action: str = Field(description="Semantic action (e.g. 'gmail.read_inbox', 'research.search', 'notify_user')")
    tool: Optional[str] = Field(default=None, description="Optional registered tool binding")
    agent: Optional[str] = Field(default=None, description="Optional agent descriptor: 'computer', 'browser', 'research', 'coder'")
    input_template: Dict[str, Any] = Field(default_factory=dict, description="Input parameters, supports {{context.var}}")
    expected_outcome: str = ""
    timeout_seconds: float = 60.0
    retry_count: int = 1
    idempotency_key: Optional[str] = Field(default=None, description="Template or static key preventing duplicate execution")
    failure_policy: FailurePolicy = FailurePolicy.STOP
    requires_approval: bool = False
    risk_level: RiskLevel = RiskLevel.SAFE


# ==============================================================================
# PERMISSION & NOTIFICATION POLICIES
# ==============================================================================

class AutomationPermissions(BaseModel):
    allowed_capabilities: List[str] = Field(default_factory=list)
    allowed_accounts: List[str] = Field(default_factory=list)
    allowed_devices: List[str] = Field(default_factory=list)
    allowed_applications: List[str] = Field(default_factory=list)
    allowed_file_paths: List[str] = Field(default_factory=list)
    max_risk_level: RiskLevel = RiskLevel.LOW_RISK
    preapproved_tools: List[str] = Field(default_factory=list)


class AutomationNotificationPolicy(BaseModel):
    notify_on_start: bool = False
    notify_on_complete: bool = True
    notify_on_failure: bool = True
    notify_on_approval: bool = True
    quiet_hours_enabled: bool = True
    quiet_hours_start: str = "23:00"
    quiet_hours_end: str = "07:00"
    channels: List[str] = Field(default_factory=lambda: ["desktop", "notifications"])
    voice_announcement: bool = False


# ==============================================================================
# CENTRAL AUTOMATION & RUN CONTRACTS
# ==============================================================================

class Automation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    version: int = 1
    enabled: bool = True
    status: AutomationStatus = AutomationStatus.ACTIVE
    scope: AutomationScope = AutomationScope.GLOBAL
    source: AutomationSource = AutomationSource.USER_CREATED
    owner: str = "user"
    trigger: TriggerConfig
    conditions: Optional[ConditionGroup] = None
    steps: List[AutomationStep] = Field(default_factory=list)
    permissions: AutomationPermissions = Field(default_factory=AutomationPermissions)
    notification_policy: AutomationNotificationPolicy = Field(default_factory=AutomationNotificationPolicy)
    failure_policy: FailurePolicy = FailurePolicy.STOP
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StepRunRecord(BaseModel):
    step_id: str
    name: str = ""
    tool: str = ""
    status: str = "PENDING"
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    duration_ms: float = 0.0
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    error: Optional[str] = None
    idempotency_key: Optional[str] = None


class AutomationRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    automation_id: str
    automation_name: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    status: RunStatus = RunStatus.TRIGGERED
    trigger_context: Dict[str, Any] = Field(default_factory=dict)
    steps: List[StepRunRecord] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    artifacts: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    approval_events: List[Dict[str, Any]] = Field(default_factory=list)
