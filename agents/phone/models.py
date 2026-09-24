"""Data models for Phone Agent and phone conversational context."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SocialAction(BaseModel):
    """Represents a staged social media action requiring user authorization."""
    action_id: str
    action_type: str  # "like", "comment", "post", "follow", "message", "delete"
    target_package: str
    target_context: str  # E.g. "Post by Priya Sharma: 'Outstanding AI engineering...'"
    action_payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = "prepared"  # "prepared", "approved", "rejected", "executed"
    created_at: float = Field(default_factory=time.time)
    preview_text: str = ""


class PhoneContext(BaseModel):
    """Tracks continuous mobile conversational context and foreground state."""
    current_app: Optional[str] = None
    current_package: Optional[str] = None
    current_activity: Optional[str] = None
    last_screenshot_b64: Optional[str] = None
    last_selected_element: Optional[str] = None
    current_task: Optional[str] = None
    device_status: str = "offline"
    history: List[str] = Field(default_factory=list)

    def update_foreground(self, package: str, activity: Optional[str] = None, app_name: Optional[str] = None) -> None:
        """Update current active foreground application context."""
        self.current_package = package
        self.current_activity = activity
        self.current_app = app_name or package
        self.history.append(f"{time.strftime('%H:%M:%S')} - Active: {self.current_app} ({package})")
        if len(self.history) > 20:
            self.history.pop(0)
