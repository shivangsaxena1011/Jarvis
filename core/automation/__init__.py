"""
SHIVANI Automation & Proactive Intelligence Package (Phase 15).
"""

from core.automation.engine import AutomationEngine
from core.automation.models import (
    Automation,
    AutomationNotificationPolicy,
    AutomationPermissions,
    AutomationRun,
    AutomationScope,
    AutomationSource,
    AutomationStatus,
    AutomationStep,
    ConditionGroup,
    ConditionOperator,
    ConditionPredicate,
    FailurePolicy,
    LogicalOperator,
    RunStatus,
    TimeSchedule,
    TriggerConfig,
    TriggerType,
)
from core.automation.runner import AutomationRunner
from core.automation.store import AutomationStore
from core.automation.triggers import EventTriggerMatcher, TimeTriggerEvaluator
from core.automation.worker import AutomationWorker

__all__ = [
    "AutomationEngine",
    "Automation",
    "AutomationRun",
    "AutomationStep",
    "AutomationPermissions",
    "AutomationNotificationPolicy",
    "AutomationStatus",
    "RunStatus",
    "TriggerType",
    "TriggerConfig",
    "TimeSchedule",
    "ConditionGroup",
    "ConditionPredicate",
    "ConditionOperator",
    "LogicalOperator",
    "FailurePolicy",
    "AutomationScope",
    "AutomationSource",
    "AutomationStore",
    "AutomationRunner",
    "AutomationWorker",
    "TimeTriggerEvaluator",
    "EventTriggerMatcher",
]
