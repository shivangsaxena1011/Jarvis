"""Core Device Bridge package for Android mobile phone integration."""

from core.bridge.models import (
    DeviceIdentity,
    CommandRequest,
    CommandResponse,
    UIElementNode,
    VisibleUIObservation,
    PhotoItem,
    NotificationItem,
)
from core.bridge.device_bridge import DeviceBridge
from core.bridge.mock_device import MockAndroidDevice
from core.bridge.crypto import generate_pairing_code, generate_device_token, sign_payload, verify_signature

__all__ = [
    "DeviceIdentity",
    "CommandRequest",
    "CommandResponse",
    "UIElementNode",
    "VisibleUIObservation",
    "PhotoItem",
    "NotificationItem",
    "DeviceBridge",
    "MockAndroidDevice",
    "generate_pairing_code",
    "generate_device_token",
    "sign_payload",
    "verify_signature",
]
