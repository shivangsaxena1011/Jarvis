"""
SHIVANI Security Events
Defines specialized security event types and notification payloads.
"""

from enum import Enum
from typing import Any, Dict, Optional
from core.events.bus import EventBus, EventType, get_event_bus


class SecurityEventType(str, Enum):
    PROMPT_INJECTION_DETECTED = "security.prompt_injection_detected"
    PATH_TRAVERSAL_BLOCKED = "security.path_traversal_blocked"
    COMMAND_BLOCKED = "security.command_blocked"
    SECRET_ACCESSED = "security.secret_accessed"
    PERMISSION_DENIED = "security.permission_denied"
    EMERGENCY_STOP_TRIGGERED = "security.emergency_stop_triggered"


class SecurityEventDispatcher:
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.bus = event_bus or get_event_bus()

    def dispatch(
        self,
        event_type: SecurityEventType,
        details: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> None:
        try:
            self.bus.publish(
                EventType.TASK_FAILED if "blocked" in event_type.value or "denied" in event_type.value else EventType.TASK_STARTED,
                task_id=task_id,
                data={"security_event": event_type.value, "details": details},
            )
        except Exception:
            pass
