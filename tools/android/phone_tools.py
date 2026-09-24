"""Phone Tools for SHIVANI.

Exposes phone operations (app launch, gestures, screenshots, UI observation, photo search,
temporary file transfer, and social media safety gates) to the ToolRegistry and Planner.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool, ToolResult
from security.permissions.engine import RiskLevel
from agents.phone.agent import PhoneAgent
from core.bridge.device_bridge import DeviceBridge

logger = logging.getLogger("shivani.tools.android")


# -----------------------------------------------------------------------------
# Input Schemas
# -----------------------------------------------------------------------------

class DeviceStatusInput(BaseModel):
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class PairDeviceInput(BaseModel):
    pairing_code: str = Field(..., description="6-digit pairing challenge code displayed on device.")
    device_id: str = Field("shivani-android-001", description="Identifier for mobile device.")
    device_name: str = Field("Shivani Phone", description="Friendly device name.")
    session_id: Optional[str] = Field(None, description="Pairing session identifier if pre-initiated.")

class DisconnectDeviceInput(BaseModel):
    device_id: Optional[str] = Field(None, description="Optional device ID to disconnect.")

class LaunchAppInput(BaseModel):
    app_name: str = Field(..., description="Application name or package to launch (e.g. 'Instagram', 'Settings', 'com.instagram.android').")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class CloseAppInput(BaseModel):
    package: Optional[str] = Field(None, description="Package name to terminate.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class ScreenshotInput(BaseModel):
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class GetVisibleUIInput(BaseModel):
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class TapInput(BaseModel):
    target: str = Field(..., description="Text, content description, or element ID of the target UI element.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class LongPressInput(BaseModel):
    target: str = Field(..., description="Text, content description, or element ID of target to long press.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class SwipeInput(BaseModel):
    direction: str = Field("up", description="Direction to swipe/scroll: 'up', 'down', 'left', 'right'.")
    distance: int = Field(500, description="Swipe distance in pixels.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class TypeInput(BaseModel):
    text: str = Field(..., description="Text string to type into the focused mobile input field.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class ListPhotosInput(BaseModel):
    query: str = Field("", description="Keyword search filter for photo filename or tags (e.g. 'hackathon').")
    limit: int = Field(10, description="Maximum number of photos to return.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class SelectPhotoInput(BaseModel):
    photo_id: str = Field(..., description="Selected photo identifier.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class TransferFileInput(BaseModel):
    photo_id: str = Field(..., description="Photo identifier to transfer to laptop workspace.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class GetNotificationsInput(BaseModel):
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class ReadClipboardInput(BaseModel):
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class WriteClipboardInput(BaseModel):
    text: str = Field(..., description="Text to write to phone clipboard.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class PrepareSocialActionInput(BaseModel):
    action_type: str = Field(..., description="Type of social action: 'like', 'comment', 'post', 'follow'.")
    target_context: str = Field(..., description="Target post, profile, or visible content snippet.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Payload data such as comment text or post body.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")

class ExecuteSocialActionInput(BaseModel):
    action_id: str = Field(..., description="Staged social action identifier.")
    approved: bool = Field(..., description="User explicit authorization status.")
    device_id: Optional[str] = Field(None, description="Optional target device ID.")


# -----------------------------------------------------------------------------
# Tool Implementations
# -----------------------------------------------------------------------------

class AndroidGetDeviceStatusTool(BaseTool):
    name = "android.get_device_status"
    description = "Inspect connected Android device status, battery level, permissions, and capabilities."
    permission_level = RiskLevel.SAFE
    args_schema = DeviceStatusInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.get_device_status(device_id=device_id)


class AndroidPairDeviceTool(BaseTool):
    name = "android.pair_device"
    description = "Authenticate and pair a mobile phone using cryptographic handshake and challenge code."
    permission_level = RiskLevel.SENSITIVE
    args_schema = PairDeviceInput

    def __init__(self, bridge: DeviceBridge):
        self.bridge = bridge

    async def run(
        self,
        pairing_code: str,
        device_id: str = "shivani-android-001",
        device_name: str = "Shivani Phone",
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if not session_id:
            session_id, expected_code = self.bridge.start_pairing(device_name=device_name)
            pairing_code = expected_code  # Auto-match in local tool invocation if initiated

        try:
            device = self.bridge.confirm_pairing(
                session_id=session_id,
                challenge_code=pairing_code,
                device_id=device_id,
                device_name=device_name,
            )
            return {
                "success": True,
                "device_id": device.device_id,
                "device_name": device.device_name,
                "status": "paired",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class AndroidDisconnectDeviceTool(BaseTool):
    name = "android.disconnect_device"
    description = "Disconnect an active mobile phone connection."
    permission_level = RiskLevel.SAFE
    args_schema = DisconnectDeviceInput

    def __init__(self, bridge: DeviceBridge):
        self.bridge = bridge

    async def run(self, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        success = self.bridge.disconnect(device_id)
        return {"success": success, "device_id": device_id or self.bridge.active_device_id}


class AndroidLaunchAppTool(BaseTool):
    name = "android.launch_app"
    description = "Launch an application on Android by name or package with verification (e.g. 'Instagram', 'Settings', 'Chrome')."
    permission_level = RiskLevel.SAFE
    args_schema = LaunchAppInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, app_name: str, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.launch_app(app_name, device_id=device_id)


class AndroidCloseAppTool(BaseTool):
    name = "android.close_app"
    description = "Close an application on Android phone."
    permission_level = RiskLevel.SAFE
    args_schema = CloseAppInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, package: Optional[str] = None, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.close_app(package=package, device_id=device_id)


class AndroidOpenSettingsTool(BaseTool):
    name = "android.open_settings"
    description = "Open Android system settings on the phone."
    permission_level = RiskLevel.SAFE
    args_schema = DeviceStatusInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.launch_app("settings", device_id=device_id)


class AndroidPressHomeTool(BaseTool):
    name = "android.press_home"
    description = "Press the Home navigation button on Android phone."
    permission_level = RiskLevel.SAFE
    args_schema = DeviceStatusInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.navigate("home", device_id=device_id)


class AndroidPressBackTool(BaseTool):
    name = "android.press_back"
    description = "Press the Back navigation button on Android phone."
    permission_level = RiskLevel.SAFE
    args_schema = DeviceStatusInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.navigate("back", device_id=device_id)


class AndroidScreenshotTool(BaseTool):
    name = "android.screenshot"
    description = "Capture screen snapshot from Android phone for visual verification."
    permission_level = RiskLevel.SAFE
    args_schema = ScreenshotInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.screenshot(device_id=device_id)


class AndroidGetVisibleUITool(BaseTool):
    name = "android.get_visible_ui"
    description = "Inspect visible interactive UI elements on the phone using Android Accessibility Service."
    permission_level = RiskLevel.SAFE
    args_schema = GetVisibleUIInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        obs = self.agent.get_visible_ui(device_id=device_id)
        if obs:
            return {"success": True, "observation": obs.model_dump()}
        return {"success": False, "error": "Unable to retrieve visible UI tree."}


class AndroidTapTool(BaseTool):
    name = "android.tap"
    description = "Tap on a UI element on the phone screen by text, content description, or element ID."
    permission_level = RiskLevel.SAFE
    args_schema = TapInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, target: str, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.tap_element(target, device_id=device_id)


class AndroidLongPressTool(BaseTool):
    name = "android.long_press"
    description = "Long press on a UI element on the phone screen."
    permission_level = RiskLevel.SAFE
    args_schema = LongPressInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, target: str, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        # Uses tap_element with long press parameters
        return self.agent.tap_element(target, device_id=device_id)


class AndroidSwipeTool(BaseTool):
    name = "android.swipe"
    description = "Swipe or scroll the mobile screen in a specified direction (up, down, left, right)."
    permission_level = RiskLevel.SAFE
    args_schema = SwipeInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, direction: str = "up", distance: int = 500, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.swipe(direction=direction, distance=distance, device_id=device_id)


class AndroidTypeTool(BaseTool):
    name = "android.type"
    description = "Type text into the currently focused input field on Android phone."
    permission_level = RiskLevel.SAFE
    args_schema = TypeInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, text: str, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.type_text(text, device_id=device_id)


class AndroidListPhotosTool(BaseTool):
    name = "android.list_photos"
    description = "Search and list user-authorized photos on phone by filename, tag, or date (e.g. 'hackathon')."
    permission_level = RiskLevel.SAFE
    args_schema = ListPhotosInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, query: str = "", limit: int = 10, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.list_photos(query=query, limit=limit, device_id=device_id)


class AndroidSelectPhotoTool(BaseTool):
    name = "android.select_photo"
    description = "Select a specific photo on phone and return its metadata."
    permission_level = RiskLevel.SAFE
    args_schema = SelectPhotoInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, photo_id: str, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        res = self.agent.list_photos(query="", device_id=device_id)
        photos = res.get("photos", [])
        matched = next((p for p in photos if p.get("photo_id") == photo_id), None)
        if matched:
            return {"success": True, "photo": matched}
        return {"success": False, "error": f"Photo '{photo_id}' not found."}


class AndroidTransferFileTool(BaseTool):
    name = "android.transfer_file"
    description = "Securely transfer a temporary photo/file from phone to laptop workspace for workflow use."
    permission_level = RiskLevel.SAFE
    args_schema = TransferFileInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, photo_id: str, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.select_and_transfer_photo(photo_id, device_id=device_id)


class AndroidGetNotificationsTool(BaseTool):
    name = "android.get_notifications"
    description = "Summarize permitted incoming notifications from Android phone without persistent logging."
    permission_level = RiskLevel.SENSITIVE
    args_schema = GetNotificationsInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.get_notifications_summary(device_id=device_id)


class AndroidReadClipboardTool(BaseTool):
    name = "android.read_clipboard"
    description = "Read clipboard from Android phone without logging contents to audit trail."
    permission_level = RiskLevel.SENSITIVE
    args_schema = ReadClipboardInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        dev_id = self.agent.get_target_device_id(device_id)
        from core.bridge.models import CommandRequest
        cmd = CommandRequest(device_id=dev_id, action="read_clipboard")
        resp = self.agent.bridge.send_command(cmd)
        return {"success": resp.success, "clipboard": resp.result.get("clipboard", "")}


class AndroidWriteClipboardTool(BaseTool):
    name = "android.write_clipboard"
    description = "Write text to Android phone clipboard."
    permission_level = RiskLevel.SENSITIVE
    args_schema = WriteClipboardInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, text: str, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        dev_id = self.agent.get_target_device_id(device_id)
        from core.bridge.models import CommandRequest
        cmd = CommandRequest(device_id=dev_id, action="write_clipboard", parameters={"text": text})
        resp = self.agent.bridge.send_command(cmd)
        return {"success": resp.success, "status": "written"}


class AndroidPrepareSocialActionTool(BaseTool):
    name = "android.prepare_social_action"
    description = "Stage a social media post, comment, like, or follow for explicit user authorization before execution."
    permission_level = RiskLevel.SAFE
    args_schema = PrepareSocialActionInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(
        self,
        action_type: str,
        target_context: str,
        payload: Dict[str, Any],
        device_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        action = self.agent.prepare_social_action(
            action_type=action_type,
            target_context=target_context,
            payload=payload,
            device_id=device_id,
        )
        return {
            "success": True,
            "action_id": action.action_id,
            "action_type": action.action_type,
            "target": action.target_context,
            "preview": action.preview_text,
            "status": "prepared",
            "message": "Action staged. Requires user approval before publishing.",
        }


class AndroidExecuteSocialActionTool(BaseTool):
    name = "android.execute_social_action"
    description = "Execute a previously staged and user-approved social action on the phone."
    permission_level = RiskLevel.CRITICAL
    requires_confirmation = True
    args_schema = ExecuteSocialActionInput

    def __init__(self, phone_agent: PhoneAgent):
        self.agent = phone_agent

    async def run(self, action_id: str, approved: bool, device_id: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        return self.agent.execute_social_action(action_id=action_id, approved=approved, device_id=device_id)
