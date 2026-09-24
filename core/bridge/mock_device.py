"""Mock Android Device Service for laptop-side unit and integration testing.

Simulates an Android 14+ smartphone with realistic package manager, accessibility tree,
input gesture execution, screenshot capture, photo library, and cancellation support.
"""

from __future__ import annotations

import base64
import os
import time
from typing import Any, Dict, List, Optional

from core.bridge.models import (
    CommandRequest,
    CommandResponse,
    NotificationItem,
    PhotoItem,
    UIElementNode,
    VisibleUIObservation,
)


class MockAndroidDevice:
    """Simulates an Android smartphone runtime for development and automated testing."""

    def __init__(self, device_id: str = "shivani-android-001", device_name: str = "Shivani Phone"):
        self.device_id = device_id
        self.device_name = device_name
        self.battery_level = 88
        self.active_package = "com.google.android.apps.nexuslauncher"
        self.active_activity = ".NexusLauncherActivity"
        self.is_task_cancelled = False
        self.clipboard_content = ""

        # Installed package registry
        self.installed_packages = {
            "com.instagram.android": "Instagram",
            "com.linkedin.android": "LinkedIn",
            "com.android.settings": "Settings",
            "com.google.android.apps.photos": "Photos",
            "com.google.android.youtube": "YouTube",
            "com.android.chrome": "Chrome",
            "com.whatsapp": "WhatsApp",
        }

        # Simulated photo library
        self.photos: List[PhotoItem] = [
            PhotoItem(
                photo_id="photo-101",
                filename="ET_Hackathon_Winner_Team.jpg",
                date_taken="2026-09-20 18:30:00",
                file_size_bytes=3421500,
                width=3840,
                height=2160,
                tags=["hackathon", "award", "team", "et hackathon"],
            ),
            PhotoItem(
                photo_id="photo-102",
                filename="ET_Hackathon_Keynote_Presentation.jpg",
                date_taken="2026-09-20 14:15:00",
                file_size_bytes=2890100,
                width=3840,
                height=2160,
                tags=["hackathon", "presentation", "stage", "et hackathon"],
            ),
            PhotoItem(
                photo_id="photo-103",
                filename="Shivani_AI_Architecture_Diagram.png",
                date_taken="2026-09-22 11:00:00",
                file_size_bytes=1542000,
                width=1920,
                height=1080,
                tags=["architecture", "diagram", "code", "ai"],
            ),
        ]

        # Simulated permitted notifications
        self.notifications: List[NotificationItem] = [
            NotificationItem(
                notification_id="notif-1",
                package_name="com.instagram.android",
                app_title="Instagram",
                title="New Message",
                text_content="Aarav sent you a direct message: 'Super excited for the demo!'",
            ),
            NotificationItem(
                notification_id="notif-2",
                package_name="com.linkedin.android",
                app_title="LinkedIn",
                title="Post Update",
                text_content="Priya Sharma commented: 'Outstanding AI engineering architecture!'",
            ),
        ]

    def handle_command(self, cmd: CommandRequest) -> CommandResponse:
        """Route incoming command request to simulated mobile execution handler."""
        action = cmd.action
        params = cmd.parameters

        if action == "cancel_task":
            self.is_task_cancelled = True
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={"status": "cancelled", "message": "Mobile task aborted successfully."},
            )

        if action == "get_device_status":
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={
                    "device_id": self.device_id,
                    "device_name": self.device_name,
                    "battery_level": self.battery_level,
                    "active_package": self.active_package,
                    "active_activity": self.active_activity,
                    "permissions": {
                        "accessibility": True,
                        "photos": True,
                        "notifications": True,
                        "storage": True,
                    },
                    "capabilities": [
                        "launch_app",
                        "close_app",
                        "screenshot",
                        "accessibility",
                        "gestures",
                        "photos",
                        "notifications",
                        "clipboard",
                    ],
                },
            )

        if action == "launch_app":
            package = params.get("package")
            if not package or package not in self.installed_packages:
                return CommandResponse(
                    request_id=cmd.request_id,
                    device_id=self.device_id,
                    success=False,
                    error=f"App package '{package}' is not installed on device.",
                )
            self.active_package = package
            self.active_activity = f"{package}.MainActivity"
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={
                    "package": self.active_package,
                    "activity": self.active_activity,
                    "app_name": self.installed_packages[package],
                    "status": "launched_and_verified",
                },
            )

        if action == "close_app":
            package = params.get("package", self.active_package)
            if self.active_package == package:
                self.active_package = "com.google.android.apps.nexuslauncher"
                self.active_activity = ".NexusLauncherActivity"
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={"package": package, "status": "closed"},
            )

        if action == "press_home":
            self.active_package = "com.google.android.apps.nexuslauncher"
            self.active_activity = ".NexusLauncherActivity"
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={"navigated": "home", "package": self.active_package},
            )

        if action == "press_back":
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={"navigated": "back", "active_package": self.active_package},
            )

        if action == "screenshot":
            # Generate minimal valid PNG placeholder header
            dummy_png_bytes = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
                b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            b64_img = base64.b64encode(dummy_png_bytes).decode("ascii")
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={
                    "format": "png",
                    "width": 1080,
                    "height": 2400,
                    "image_b64": b64_img,
                    "package": self.active_package,
                },
            )

        if action == "get_visible_ui":
            observation = self._generate_ui_observation()
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result=observation.model_dump(),
            )

        if action in ("tap", "long_press"):
            target_text = params.get("text", "")
            element_id = params.get("element_id", "")
            x = params.get("x")
            y = params.get("y")

            # Check if tapping Instagram direct message icon or settings
            if "Direct" in target_text or "message" in target_text.lower():
                self.active_activity = "com.instagram.android.DirectMessagesActivity"
            elif "Profile" in target_text:
                self.active_activity = "com.instagram.android.ProfileActivity"

            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={
                    "action": action,
                    "target_text": target_text,
                    "element_id": element_id,
                    "coordinates": [x or 540, y or 960],
                    "active_activity": self.active_activity,
                },
            )

        if action == "type":
            text = params.get("text", "")
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={"action": "type", "text_length": len(text), "status": "text_committed"},
            )

        if action == "swipe":
            direction = params.get("direction", "up")
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={"action": "swipe", "direction": direction, "distance": params.get("distance", 500)},
            )

        if action == "list_photos":
            query = params.get("query", "").lower()
            limit = params.get("limit", 10)
            matched = []
            for photo in self.photos:
                if not query:
                    matched.append(photo.model_dump())
                else:
                    if query in photo.filename.lower() or any(query in tag.lower() for tag in photo.tags):
                        matched.append(photo.model_dump())
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={"count": len(matched[:limit]), "photos": matched[:limit]},
            )

        if action == "transfer_file":
            photo_id = params.get("photo_id")
            target_photo = next((p for p in self.photos if p.photo_id == photo_id), None)
            if not target_photo:
                return CommandResponse(
                    request_id=cmd.request_id,
                    device_id=self.device_id,
                    success=False,
                    error=f"Photo with ID '{photo_id}' not found.",
                )

            # Create simulated temporary file transfer destination in workspace
            temp_dir = os.path.join("workspace", "shivani-artifacts", "temp_transfers")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, target_photo.filename)
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(f"Simulated binary transfer of photo {target_photo.filename}\n")

            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={
                    "photo_id": photo_id,
                    "filename": target_photo.filename,
                    "local_path": os.path.abspath(temp_file),
                    "bytes_transferred": target_photo.file_size_bytes,
                },
            )

        if action == "get_notifications":
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={
                    "count": len(self.notifications),
                    "notifications": [n.model_dump() for n in self.notifications],
                },
            )

        if action == "read_clipboard":
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={"clipboard": self.clipboard_content},
            )

        if action == "write_clipboard":
            text = params.get("text", "")
            self.clipboard_content = text
            return CommandResponse(
                request_id=cmd.request_id,
                device_id=self.device_id,
                success=True,
                result={"status": "written", "text_length": len(text)},
            )

        return CommandResponse(
            request_id=cmd.request_id,
            device_id=self.device_id,
            success=False,
            error=f"Unsupported action '{action}' on MockAndroidDevice.",
        )

    def _generate_ui_observation(self) -> VisibleUIObservation:
        """Produce context-aware minimal UI node trees based on foreground app and activity."""
        elements: List[UIElementNode] = []

        if self.active_package == "com.instagram.android":
            if "DirectMessagesActivity" in self.active_activity:
                elements = [
                    UIElementNode(element_id="hdr_dm", type="text_view", text="Messages", bounds=[40, 100, 300, 160]),
                    UIElementNode(
                        element_id="msg_1",
                        type="text_view",
                        text="Aarav: Super excited for the demo!",
                        clickable=True,
                        bounds=[40, 200, 1000, 280],
                    ),
                    UIElementNode(
                        element_id="msg_2",
                        type="text_view",
                        text="Rohan: Are we on track for tomorrow?",
                        clickable=True,
                        bounds=[40, 300, 1000, 380],
                    ),
                    UIElementNode(
                        element_id="btn_back",
                        type="button",
                        content_desc="Back",
                        clickable=True,
                        bounds=[10, 100, 60, 160],
                    ),
                ]
            elif "ProfileActivity" in self.active_activity:
                elements = [
                    UIElementNode(element_id="profile_name", type="text_view", text="Shivani AI Dev", bounds=[100, 120, 500, 180]),
                    UIElementNode(element_id="btn_edit", type="button", text="Edit profile", clickable=True, bounds=[60, 220, 480, 280]),
                    UIElementNode(element_id="btn_share", type="button", text="Share profile", clickable=True, bounds=[520, 220, 940, 280]),
                ]
            else:  # FeedActivity
                elements = [
                    UIElementNode(element_id="top_logo", type="image", content_desc="Instagram", bounds=[40, 80, 260, 160]),
                    UIElementNode(
                        element_id="btn_messages",
                        type="button",
                        content_desc="Direct Messages",
                        clickable=True,
                        bounds=[940, 80, 1040, 160],
                    ),
                    UIElementNode(
                        element_id="feed_post_1",
                        type="text_view",
                        text="DeepMind announces next-gen agent models!",
                        bounds=[40, 300, 1040, 450],
                    ),
                    UIElementNode(element_id="btn_like", type="button", content_desc="Like", clickable=True, bounds=[40, 800, 120, 880]),
                    UIElementNode(element_id="btn_comment", type="button", content_desc="Comment", clickable=True, bounds=[140, 800, 220, 880]),
                    UIElementNode(element_id="btn_profile", type="button", content_desc="Profile", clickable=True, bounds=[880, 2200, 1000, 2320]),
                ]

        elif self.active_package == "com.android.settings":
            elements = [
                UIElementNode(element_id="set_title", type="text_view", text="Settings", bounds=[60, 120, 400, 200]),
                UIElementNode(element_id="set_wifi", type="text_view", text="Network & internet", clickable=True, bounds=[60, 240, 1000, 320]),
                UIElementNode(element_id="set_apps", type="text_view", text="Apps", clickable=True, bounds=[60, 340, 1000, 420]),
                UIElementNode(
                    element_id="set_access",
                    type="text_view",
                    text="Accessibility",
                    clickable=True,
                    bounds=[60, 440, 1000, 520],
                ),
            ]

        elif self.active_package == "com.linkedin.android":
            elements = [
                UIElementNode(element_id="li_search", type="edit_text", text="Search", clickable=True, bounds=[60, 80, 800, 160]),
                UIElementNode(
                    element_id="li_post_text",
                    type="text_view",
                    text="Excited to present SHIVANI autonomous computer agent.",
                    bounds=[60, 300, 1020, 500],
                ),
                UIElementNode(element_id="btn_li_like", type="button", text="Like", clickable=True, bounds=[60, 800, 200, 880]),
                UIElementNode(element_id="btn_li_comment", type="button", text="Comment", clickable=True, bounds=[240, 800, 400, 880]),
            ]

        else:
            elements = [
                UIElementNode(element_id="launcher_search", type="text_view", text="Search apps", clickable=True, bounds=[60, 100, 1020, 180]),
                UIElementNode(element_id="app_instagram", type="button", text="Instagram", clickable=True, bounds=[80, 300, 240, 460]),
                UIElementNode(element_id="app_settings", type="button", text="Settings", clickable=True, bounds=[280, 300, 440, 460]),
                UIElementNode(element_id="app_photos", type="button", text="Photos", clickable=True, bounds=[480, 300, 640, 460]),
            ]

        return VisibleUIObservation(
            package_name=self.active_package,
            activity_name=self.active_activity,
            elements=elements,
            window_title=self.installed_packages.get(self.active_package, "Launcher"),
        )
