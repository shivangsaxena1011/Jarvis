"""
SHIVANI Notification Center
Central notification hub supporting priorities (INFO, SUCCESS, WARNING, ACTION_REQUIRED, ERROR),
event bus emissions, and callback subscriptions for UI and automation pipelines.
"""

from datetime import datetime, timezone
from enum import Enum
import threading
from typing import Any, Callable, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class NotificationCategory(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ACTION_REQUIRED = "action_required"
    ERROR = "error"


class NotificationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    message: str
    category: NotificationCategory = NotificationCategory.INFO
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False
    dismissed: bool = False
    action_payload: Optional[Dict[str, Any]] = None


class NotificationCenter:
    def __init__(self, event_bus: Optional[Any] = None):
        self.event_bus = event_bus
        self._notifications: List[NotificationItem] = []
        self._listeners: List[Callable[[NotificationItem], None]] = []
        self._lock = threading.Lock()

    def subscribe(self, callback: Callable[[NotificationItem], None]) -> None:
        with self._lock:
            self._listeners.append(callback)

    def notify(
        self,
        title: str,
        message: str,
        category: NotificationCategory = NotificationCategory.INFO,
        action_payload: Optional[Dict[str, Any]] = None,
    ) -> NotificationItem:
        item = NotificationItem(
            title=title,
            message=message,
            category=category,
            action_payload=action_payload,
        )
        with self._lock:
            self._notifications.append(item)
            if len(self._notifications) > 200:
                self._notifications.pop(0)

        # Emit event if event bus available
        if self.event_bus:
            try:
                from core.events.bus import EventType
                self.event_bus.publish(
                    EventType.TASK_STARTED if category != NotificationCategory.ERROR else EventType.TASK_FAILED,
                    data={"notification": item.model_dump()},
                )
            except Exception:
                pass

        # Trigger subscribed listeners
        for listener in self._listeners:
            try:
                listener(item)
            except Exception:
                pass

        return item

    def list_notifications(
        self,
        unread_only: bool = False,
        category: Optional[NotificationCategory] = None,
        limit: int = 50,
    ) -> List[NotificationItem]:
        with self._lock:
            results = []
            for n in reversed(self._notifications):
                if n.dismissed:
                    continue
                if unread_only and n.read:
                    continue
                if category and n.category != category:
                    continue
                results.append(n)
                if len(results) >= limit:
                    break
            return results

    def mark_as_read(self, notification_id: str) -> bool:
        with self._lock:
            for n in self._notifications:
                if n.id == notification_id:
                    n.read = True
                    return True
            return False

    def dismiss(self, notification_id: str) -> bool:
        with self._lock:
            for n in self._notifications:
                if n.id == notification_id:
                    n.dismissed = True
                    return True
            return False

    def get_unread_count(self) -> int:
        with self._lock:
            return sum(1 for n in self._notifications if not n.read and not n.dismissed)
