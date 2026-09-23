"""
SHIVANI Event System
Lightweight asynchronous Pub/Sub Event Bus for internal decoupling and UI streaming.
"""

from enum import Enum
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    TASK_CREATED = "TASK_CREATED"
    TASK_PLANNED = "TASK_PLANNED"
    TASK_WAITING_APPROVAL = "TASK_WAITING_APPROVAL"
    TASK_STARTED = "TASK_STARTED"
    TOOL_STARTED = "TOOL_STARTED"
    TOOL_COMPLETED = "TOOL_COMPLETED"
    TOOL_FAILED = "TOOL_FAILED"
    TASK_VERIFYING = "TASK_VERIFYING"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_CANCELLED = "TASK_CANCELLED"
    SYSTEM_STATUS = "SYSTEM_STATUS"


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    task_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class EventBus:
    """Asynchronous event bus supporting listeners and live subscription queues."""

    def __init__(self, max_history: int = 500):
        self._listeners: List[Callable[[Event], Any]] = []
        self._subscriber_queues: List[asyncio.Queue] = []
        self._history: List[Event] = []
        self._max_history = max_history

    def subscribe(self, callback: Callable[[Event], Any]) -> None:
        """Register a synchronous or async callback."""
        self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[Event], Any]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def create_subscription_queue(self) -> asyncio.Queue:
        """Creates a queue for streaming (e.g. SSE endpoints)."""
        queue = asyncio.Queue()
        self._subscriber_queues.append(queue)
        return queue

    def remove_subscription_queue(self, queue: asyncio.Queue) -> None:
        if queue in self._subscriber_queues:
            self._subscriber_queues.remove(queue)

    def publish(
        self,
        event_type: EventType | str,
        task_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Event:
        if isinstance(event_type, str):
            event_type = EventType(event_type)

        event = Event(
            event_type=event_type,
            task_id=task_id,
            data=data or {}
        )

        # Store in bounded history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # Notify callbacks
        for listener in list(self._listeners):
            try:
                res = listener(event)
                if asyncio.iscoroutine(res):
                    asyncio.create_task(res)
            except Exception as e:
                print(f"[EVENT BUS ERROR] Listener failed: {e}")

        # Push to stream queues
        for queue in list(self._subscriber_queues):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

        return event

    def get_history(self, limit: int = 50, task_id: Optional[str] = None) -> List[Event]:
        events = self._history
        if task_id:
            events = [e for e in events if e.task_id == task_id]
        return events[-limit:]


# Global singleton event bus
_global_bus = EventBus()

def get_event_bus() -> EventBus:
    return _global_bus
