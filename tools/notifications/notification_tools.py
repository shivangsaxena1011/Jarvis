"""
SHIVANI Notification Tools
Registered tools for retrieving and managing user notifications and action-required alerts.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from notifications.center import NotificationCenter


class NotificationsListArgs(BaseModel):
    unread_only: bool = Field(default=False, description="Filter to only unread notifications")
    limit: int = Field(default=20, description="Max notifications to retrieve")


class NotificationsListTool(BaseTool):
    name = "notifications.list"
    description = "Lists active notifications, alerts, and pending action requests."
    permission_level = RiskLevel.SAFE
    args_schema = NotificationsListArgs
    timeout = 10.0

    def __init__(self, notification_center: Optional[NotificationCenter] = None):
        super().__init__()
        self.center = notification_center or NotificationCenter()

    async def run(self, unread_only: bool = False, limit: int = 20) -> Dict[str, Any]:
        notifications = self.center.list_notifications(unread_only=unread_only, limit=limit)
        return {
            "count": len(notifications),
            "unread_count": self.center.get_unread_count(),
            "notifications": [n.model_dump() for n in notifications],
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": isinstance(result_data.get("notifications"), list)}


class NotificationsDismissArgs(BaseModel):
    notification_id: str = Field(description="ID of the notification to dismiss")


class NotificationsDismissTool(BaseTool):
    name = "notifications.dismiss"
    description = "Dismisses a notification by its ID."
    permission_level = RiskLevel.SAFE
    args_schema = NotificationsDismissArgs
    timeout = 10.0

    def __init__(self, notification_center: Optional[NotificationCenter] = None):
        super().__init__()
        self.center = notification_center or NotificationCenter()

    async def run(self, notification_id: str) -> Dict[str, Any]:
        dismissed = self.center.dismiss(notification_id)
        return {"dismissed": dismissed, "notification_id": notification_id}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("dismissed"))}
