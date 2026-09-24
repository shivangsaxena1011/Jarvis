"""Device Bridge Protocol & Data Models.

Defines the structured communication protocol, device identity, command request/response,
and minimal UI observation structures for the secure Android Device Bridge.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DeviceIdentity(BaseModel):
    """Represents a paired or discoverable device."""
    device_id: str
    device_name: str
    platform: str = "android"
    capabilities: List[str] = Field(default_factory=lambda: [
        "launch_app",
        "close_app",
        "screenshot",
        "accessibility",
        "gestures",
        "photos",
        "notifications",
        "clipboard"
    ])
    pairing_state: str = "unpaired"  # "unpaired", "pairing", "paired", "rejected"
    connection_status: str = "offline"  # "connected", "offline", "disconnected"
    last_seen: float = Field(default_factory=time.time)
    battery_level: Optional[int] = 100
    ip_address: Optional[str] = "127.0.0.1"
    port: int = 8765
    public_key: Optional[str] = None
    auth_token: Optional[str] = None


class CommandRequest(BaseModel):
    """Structured request payload sent to a mobile device."""
    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:12]}")
    device_id: str
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class CommandResponse(BaseModel):
    """Structured response received from a mobile device."""
    request_id: str
    device_id: str
    success: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class UIElementNode(BaseModel):
    """Minimal representation of a visible interactive UI element."""
    element_id: str
    type: str  # "button", "text_view", "edit_text", "image", "list_item", "layout"
    text: str = ""
    content_desc: str = ""
    resource_id: str = ""
    clickable: bool = False
    focusable: bool = False
    scrollable: bool = False
    bounds: List[int] = Field(default_factory=lambda: [0, 0, 0, 0])  # [left, top, right, bottom]
    children: List[UIElementNode] = Field(default_factory=list)


class VisibleUIObservation(BaseModel):
    """Minimal UI tree observation captured from Android Accessibility Service."""
    package_name: str
    activity_name: str
    elements: List[UIElementNode] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    window_title: Optional[str] = ""


class PhotoItem(BaseModel):
    """Metadata describing a photo stored on the device."""
    photo_id: str
    filename: str
    date_taken: str
    file_size_bytes: int = 0
    width: int = 1920
    height: int = 1080
    tags: List[str] = Field(default_factory=list)
    thumbnail_b64: Optional[str] = None
    local_temp_path: Optional[str] = None


class NotificationItem(BaseModel):
    """Permitted notification model."""
    notification_id: str
    package_name: str
    app_title: str
    title: str
    text_content: str
    timestamp: float = Field(default_factory=time.time)
