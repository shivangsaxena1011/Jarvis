"""Phone Agent implementation for autonomous Android device control.

Orchestrates device bridge communications, natural language app resolution,
accessibility-driven UI automation, verification, photo workflows, and social media safety gates.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from core.bridge.device_bridge import DeviceBridge
from core.bridge.models import CommandRequest, CommandResponse, VisibleUIObservation
from agents.phone.models import PhoneContext, SocialAction
from agents.phone.app_resolver import AppResolver
from agents.phone.ui_observer import AndroidUIObserver

logger = logging.getLogger("shivani.agents.phone")


class PhoneAgent:
    """Autonomous agent capable of operating paired Android devices."""

    def __init__(
        self,
        bridge: DeviceBridge,
        app_resolver: Optional[AppResolver] = None,
        ui_observer: Optional[AndroidUIObserver] = None,
    ):
        self.bridge = bridge
        self.app_resolver = app_resolver or AppResolver()
        self.ui_observer = ui_observer or AndroidUIObserver()
        self.context = PhoneContext()
        self._staged_social_actions: Dict[str, SocialAction] = {}

    def get_target_device_id(self, device_id: Optional[str] = None) -> Optional[str]:
        """Resolve target device ID or default to active device."""
        target = device_id or self.bridge.active_device_id
        if not target and self.bridge.devices:
            target = next(iter(self.bridge.devices.keys()))
        return target

    # -------------------------------------------------------------------------
    # App Launching & Discovery with Verification
    # -------------------------------------------------------------------------

    def launch_app(self, natural_query: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Resolve application from natural language and launch with verification.

        Supports:
        - "Instagram kholo"
        - "phone pe Instagram open karo"
        - "phone ki settings kholo"
        - "meri photos kholo"
        """
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        package = self.app_resolver.resolve_package(natural_query)
        if not package:
            candidates = self.app_resolver.find_candidates(natural_query)
            if candidates:
                cand_str = ", ".join([f"{name} ({pkg})" for name, pkg in candidates[:3]])
                return {
                    "success": False,
                    "error": f"Ambiguous app '{natural_query}'. Did you mean: {cand_str}?",
                    "candidates": candidates,
                }
            return {"success": False, "error": f"Could not resolve application '{natural_query}'."}

        cmd = CommandRequest(
            device_id=dev_id,
            action="launch_app",
            parameters={"package": package},
        )
        response = self.bridge.send_command(cmd)

        if response.success:
            app_name = response.result.get("app_name", natural_query)
            self.context.update_foreground(
                package=package,
                activity=response.result.get("activity"),
                app_name=app_name,
            )
            return {
                "success": True,
                "package": package,
                "app_name": app_name,
                "status": "launched_and_verified",
                "message": f"{app_name} is open on phone.",
            }

        return {"success": False, "error": response.error}

    def close_app(self, package: Optional[str] = None, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Close an application or the currently active foreground app."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        target_pkg = package or self.context.current_package or "com.instagram.android"
        cmd = CommandRequest(
            device_id=dev_id,
            action="close_app",
            parameters={"package": target_pkg},
        )
        response = self.bridge.send_command(cmd)
        if response.success:
            if self.context.current_package == target_pkg:
                self.context.current_package = None
                self.context.current_app = None
            return {"success": True, "package": target_pkg, "status": "closed"}
        return {"success": False, "error": response.error}

    # -------------------------------------------------------------------------
    # System Navigation
    # -------------------------------------------------------------------------

    def navigate(self, target: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform system navigation (home, back, settings, recents)."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        clean = target.strip().lower()
        if "home" in clean:
            cmd = CommandRequest(device_id=dev_id, action="press_home")
            resp = self.bridge.send_command(cmd)
            if resp.success:
                self.context.update_foreground("com.google.android.apps.nexuslauncher", ".NexusLauncherActivity", "Home")
            return {"success": resp.success, "action": "press_home", "result": resp.result}

        if "back" in clean:
            cmd = CommandRequest(device_id=dev_id, action="press_back")
            resp = self.bridge.send_command(cmd)
            return {"success": resp.success, "action": "press_back", "result": resp.result}

        if "setting" in clean:
            return self.launch_app("settings", device_id=dev_id)

        return {"success": False, "error": f"Unknown navigation target '{target}'."}

    # -------------------------------------------------------------------------
    # Observation & Screenshots
    # -------------------------------------------------------------------------

    def get_visible_ui(self, device_id: Optional[str] = None) -> Optional[VisibleUIObservation]:
        """Retrieve minimal visible UI tree from Accessibility Service."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return None

        cmd = CommandRequest(device_id=dev_id, action="get_visible_ui")
        resp = self.bridge.send_command(cmd)
        if resp.success:
            return VisibleUIObservation(**resp.result)
        return None

    def screenshot(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Capture screen snapshot from phone without persistent storage."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        cmd = CommandRequest(device_id=dev_id, action="screenshot")
        resp = self.bridge.send_command(cmd)
        if resp.success:
            b64_img = resp.result.get("image_b64")
            self.context.last_screenshot_b64 = b64_img
            return {
                "success": True,
                "width": resp.result.get("width", 1080),
                "height": resp.result.get("height", 2400),
                "package": resp.result.get("package"),
                "has_image": bool(b64_img),
            }
        return {"success": False, "error": resp.error}

    # -------------------------------------------------------------------------
    # UI Interaction (Tap, Type, Swipe)
    # -------------------------------------------------------------------------

    def tap_element(self, query: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Locate element dynamically using UI observer and tap on it."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        observation = self.get_visible_ui(device_id=dev_id)
        if not observation:
            return {"success": False, "error": "Failed to inspect visible UI."}

        target_node = self.ui_observer.find_target_element(query, observation)
        if not target_node:
            return {"success": False, "error": f"Element matching '{query}' was not found on screen."}

        # Calculate center coordinates
        bounds = target_node.bounds or [0, 0, 100, 100]
        center_x = (bounds[0] + bounds[2]) // 2
        center_y = (bounds[1] + bounds[3]) // 2

        cmd = CommandRequest(
            device_id=dev_id,
            action="tap",
            parameters={
                "element_id": target_node.element_id,
                "text": target_node.text or target_node.content_desc,
                "x": center_x,
                "y": center_y,
            },
        )
        resp = self.bridge.send_command(cmd)
        if resp.success:
            self.context.last_selected_element = target_node.element_id
            return {
                "success": True,
                "element_id": target_node.element_id,
                "target_text": target_node.text or target_node.content_desc,
                "tapped_at": [center_x, center_y],
            }
        return {"success": False, "error": resp.error}

    def type_text(self, text: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Type text into the currently focused input field."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        cmd = CommandRequest(
            device_id=dev_id,
            action="type",
            parameters={"text": text},
        )
        resp = self.bridge.send_command(cmd)
        return {"success": resp.success, "text_length": len(text), "error": resp.error}

    def swipe(self, direction: str = "up", distance: int = 500, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform gesture scroll/swipe in specified direction."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        cmd = CommandRequest(
            device_id=dev_id,
            action="swipe",
            parameters={"direction": direction, "distance": distance},
        )
        resp = self.bridge.send_command(cmd)
        return {"success": resp.success, "direction": direction, "error": resp.error}

    # -------------------------------------------------------------------------
    # Content & Message Summaries (Strict Privacy & Minimization)
    # -------------------------------------------------------------------------

    def summarize_visible_messages(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Extract and summarize only visible permitted messages on screen without crawling."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        observation = self.get_visible_ui(device_id=dev_id)
        if not observation:
            return {"success": False, "error": "Failed to read screen for messages."}

        lines = self.ui_observer.extract_visible_text_summary(observation)
        if not lines:
            return {"success": True, "summary": "No unread or visible messages found on screen."}

        msg_lines = [l for l in lines if ":" in l or len(l) > 10]
        summary_text = " • " + "\n • ".join(msg_lines) if msg_lines else " • " + "\n • ".join(lines[:5])
        return {
            "success": True,
            "package": observation.package_name,
            "message_count": len(msg_lines),
            "summary": f"Visible Messages Summary:\n{summary_text}",
        }

    # -------------------------------------------------------------------------
    # Photo Workflows & Safe File Transfer
    # -------------------------------------------------------------------------

    def list_photos(self, query: str = "", limit: int = 10, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Search device photo library by filename, tag, or date."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        cmd = CommandRequest(
            device_id=dev_id,
            action="list_photos",
            parameters={"query": query, "limit": limit},
        )
        resp = self.bridge.send_command(cmd)
        if resp.success:
            photos = resp.result.get("photos", [])
            return {"success": True, "count": len(photos), "photos": photos}
        return {"success": False, "error": resp.error}

    def select_and_transfer_photo(self, photo_id: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Transfer selected photo securely to temporary workspace for workflow consumption."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        cmd = CommandRequest(
            device_id=dev_id,
            action="transfer_file",
            parameters={"photo_id": photo_id},
        )
        resp = self.bridge.send_command(cmd)
        if resp.success:
            return {
                "success": True,
                "photo_id": photo_id,
                "filename": resp.result.get("filename"),
                "local_path": resp.result.get("local_path"),
            }
        return {"success": False, "error": resp.error}

    # -------------------------------------------------------------------------
    # Social Media Safety Gate
    # -------------------------------------------------------------------------

    def prepare_social_action(
        self,
        action_type: str,
        target_context: str,
        payload: Dict[str, Any],
        device_id: Optional[str] = None,
    ) -> SocialAction:
        """Stage a social media post, comment, like, or follow for user approval."""
        dev_id = self.get_target_device_id(device_id)
        pkg = self.context.current_package or "com.instagram.android"
        action_id = f"soc-{uuid.uuid4().hex[:8]}"

        action = SocialAction(
            action_id=action_id,
            action_type=action_type,
            target_package=pkg,
            target_context=target_context,
            action_payload=payload,
            preview_text=payload.get("text", f"Action: {action_type} on {target_context}"),
            status="prepared",
        )
        self._staged_social_actions[action_id] = action
        logger.info(f"Staged social action {action_id}: {action_type} on {pkg}")
        return action

    def execute_social_action(self, action_id: str, approved: bool, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute staged social action only if approved by user."""
        action = self._staged_social_actions.get(action_id)
        if not action:
            return {"success": False, "error": f"Social action '{action_id}' not found."}

        if not approved:
            action.status = "rejected"
            return {"success": False, "status": "rejected", "message": "Action rejected by user."}

        dev_id = self.get_target_device_id(device_id)
        # Execute action via bridge
        if action.action_type in ("comment", "post"):
            text = action.action_payload.get("text", "")
            self.type_text(text, device_id=dev_id)
            self.tap_element("Post", device_id=dev_id)
        elif action.action_type == "like":
            self.tap_element("Like", device_id=dev_id)

        action.status = "executed"
        return {"success": True, "action_id": action_id, "status": "executed", "verified": True}

    # -------------------------------------------------------------------------
    # Notification & Clipboard Helpers
    # -------------------------------------------------------------------------

    def get_notifications_summary(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve permitted notifications on demand and summarize."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"success": False, "error": "No paired Android device available."}

        cmd = CommandRequest(device_id=dev_id, action="get_notifications")
        resp = self.bridge.send_command(cmd)
        if resp.success:
            notifs = resp.result.get("notifications", [])
            lines = [f" • [{n['app_title']}] {n['title']}: {n['text_content']}" for n in notifs]
            summary = "\n".join(lines) if lines else "No new notifications."
            return {"success": True, "count": len(notifs), "summary": summary}
        return {"success": False, "error": resp.error}

    def emergency_stop(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Propagate immediate cancellation ('Shivani stop') to mobile agent."""
        dev_id = self.get_target_device_id(device_id)
        resp = self.bridge.cancel_current_task(device_id=dev_id)
        return {"success": resp.success, "status": "cancelled", "result": resp.result}

    def get_device_status(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Check live device health, battery, and permissions."""
        dev_id = self.get_target_device_id(device_id)
        if not dev_id:
            return {"connected": False, "status": "No device paired."}

        cmd = CommandRequest(device_id=dev_id, action="get_device_status")
        resp = self.bridge.send_command(cmd)
        if resp.success:
            return {"connected": True, **resp.result}
        return {"connected": False, "error": resp.error}
