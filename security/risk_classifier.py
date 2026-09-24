"""
SHIVANI Risk Classifier
Categorizes operations into 5 risk tiers (SAFE, LOW_RISK, SENSITIVE, HIGH_RISK, CRITICAL)
based on tool metadata, target parameters, destructive potential, and privilege scope.
"""

import re
from typing import Any, Dict, Optional
from security.permissions import RiskLevel


class RiskClassifier:
    """Classifies tool executions and user intents into standard risk tiers."""

    # Default tool risk mappings
    TOOL_RISK_MAP = {
        # Safe operations
        "computer.open_app": RiskLevel.SAFE,
        "computer.list_apps": RiskLevel.SAFE,
        "computer.active_window": RiskLevel.SAFE,
        "computer.list_windows": RiskLevel.SAFE,
        "computer.screenshot": RiskLevel.SAFE,
        "computer.mouse_move": RiskLevel.SAFE,
        "computer.get_cursor_pos": RiskLevel.SAFE,
        "filesystem.list": RiskLevel.SAFE,
        "filesystem.search": RiskLevel.SAFE,
        "filesystem.read_metadata": RiskLevel.SAFE,
        "browser.get_title": RiskLevel.SAFE,
        "browser.get_url": RiskLevel.SAFE,
        "browser.extract_text": RiskLevel.SAFE,
        "browser.extract_links": RiskLevel.SAFE,
        "browser.summarize": RiskLevel.SAFE,
        "browser.screenshot": RiskLevel.SAFE,
        "coding.inspect_project": RiskLevel.SAFE,
        "coding.search_code": RiskLevel.SAFE,
        "coding.find_symbol": RiskLevel.SAFE,
        "coding.read_code_file": RiskLevel.SAFE,
        "coding.git_status": RiskLevel.SAFE,
        "coding.git_diff": RiskLevel.SAFE,
        "research.search": RiskLevel.SAFE,
        "research.open_source": RiskLevel.SAFE,
        "research.summarize": RiskLevel.SAFE,
        "research.save": RiskLevel.SAFE,
        "presentation.generate_deck": RiskLevel.SAFE,
        "presentation.generate_pitch": RiskLevel.SAFE,
        "presentation.generate_qa": RiskLevel.SAFE,
        "documentation.generate_readme": RiskLevel.SAFE,
        "documentation.generate_api_docs": RiskLevel.SAFE,
        "documentation.generate_arch_doc": RiskLevel.SAFE,
        "phone.status": RiskLevel.SAFE,
        "phone.screenshot": RiskLevel.SAFE,
        "phone.visible_ui": RiskLevel.SAFE,
        "phone.home": RiskLevel.SAFE,
        "phone.back": RiskLevel.SAFE,
        "memory.get_preference": RiskLevel.SAFE,
        "memory.set_preference": RiskLevel.SAFE,
        "memory.search": RiskLevel.SAFE,
        "memory.explain": RiskLevel.SAFE,
        "scheduler.list_jobs": RiskLevel.SAFE,
        "notifications.list": RiskLevel.SAFE,
        "notifications.dismiss": RiskLevel.SAFE,

        # Low risk operations
        "filesystem.create_directory": RiskLevel.LOW_RISK,
        "browser.open": RiskLevel.LOW_RISK,
        "browser.navigate": RiskLevel.LOW_RISK,
        "browser.new_tab": RiskLevel.LOW_RISK,
        "browser.switch_tab": RiskLevel.LOW_RISK,
        "browser.scroll": RiskLevel.LOW_RISK,
        "linkedin.prepare_post": RiskLevel.LOW_RISK,
        "linkedin.prepare_comment": RiskLevel.LOW_RISK,
        "gmail.summarize": RiskLevel.LOW_RISK,
        "gmail.propose_cleanup": RiskLevel.LOW_RISK,
        "content.generate_linkedin_post": RiskLevel.LOW_RISK,
        "content.generate_email": RiskLevel.LOW_RISK,
        "phone.launch_app": RiskLevel.LOW_RISK,
        "phone.tap": RiskLevel.LOW_RISK,
        "phone.type": RiskLevel.LOW_RISK,
        "phone.prepare_social_action": RiskLevel.LOW_RISK,
        "scheduler.schedule_job": RiskLevel.LOW_RISK,

        # Sensitive operations
        "filesystem.read": RiskLevel.SENSITIVE,
        "filesystem.write": RiskLevel.SENSITIVE,
        "computer.clipboard_read": RiskLevel.SENSITIVE,
        "computer.clipboard_write": RiskLevel.SENSITIVE,
        "coding.apply_patch": RiskLevel.SENSITIVE,
        "coding.create_file": RiskLevel.SENSITIVE,
        "coding.run_tests": RiskLevel.SENSITIVE,
        "coding.run_build": RiskLevel.SENSITIVE,
        "coding.git_commit": RiskLevel.SENSITIVE,
        "gmail.list_unread": RiskLevel.SENSITIVE,
        "gmail.search": RiskLevel.SENSITIVE,
        "linkedin.read_feed": RiskLevel.SENSITIVE,
        "phone.list_photos": RiskLevel.SENSITIVE,
        "phone.select_photo": RiskLevel.SENSITIVE,
        "phone.read_clipboard": RiskLevel.SENSITIVE,
        "phone.get_notifications": RiskLevel.SENSITIVE,
        "memory.forget": RiskLevel.SENSITIVE,

        # High risk operations
        "filesystem.delete": RiskLevel.HIGH_RISK,
        "computer.close_app": RiskLevel.HIGH_RISK,
        "computer.close_window": RiskLevel.HIGH_RISK,
        "coding.git_push": RiskLevel.HIGH_RISK,
        "linkedin.publish_post": RiskLevel.HIGH_RISK,
        "gmail.delete": RiskLevel.HIGH_RISK,
        "gmail.execute_cleanup": RiskLevel.HIGH_RISK,
        "phone.execute_social_action": RiskLevel.HIGH_RISK,
        "phone.close_app": RiskLevel.HIGH_RISK,
        "scheduler.cancel_job": RiskLevel.HIGH_RISK,

        # Critical operations
        "terminal.execute": RiskLevel.CRITICAL,
    }

    CRITICAL_COMMAND_PATTERNS = [
        re.compile(r"\b(?:format|diskpart|reg\s+delete|mkfs|dd\s+if=)\b", re.IGNORECASE),
        re.compile(r"\b(?:rmdir\s+/[sq]\s+[a-z]:\\|rm\s+-rf\s+/)\b", re.IGNORECASE),
        re.compile(r"\b(?:net\s+user|takeown|icacls\s+.*\/grant)\b", re.IGNORECASE),
    ]

    @classmethod
    def classify_tool(cls, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> RiskLevel:
        base_risk = cls.TOOL_RISK_MAP.get(tool_name, RiskLevel.SENSITIVE)

        # Inspect specific arguments for escalation
        if tool_name == "terminal.execute" and arguments:
            cmd = str(arguments.get("command", "")).lower()
            for pattern in cls.CRITICAL_COMMAND_PATTERNS:
                if pattern.search(cmd):
                    return RiskLevel.CRITICAL
            return RiskLevel.HIGH_RISK

        if tool_name in ("filesystem.write", "coding.apply_patch") and arguments:
            path = str(arguments.get("file_path", arguments.get("path", ""))).lower()
            if any(p in path for p in ["system32", "windows", "/etc", "/usr", ".ssh"]):
                return RiskLevel.CRITICAL

        return base_risk

    @classmethod
    def classify_intent(cls, intent_text: str) -> RiskLevel:
        text_lower = intent_text.lower()
        if any(w in text_lower for w in ["format", "destroy", "wipe", "root", "admin", "privileged", "password change"]):
            return RiskLevel.CRITICAL
        if any(w in text_lower for w in ["delete", "remove", "publish", "send email", "git push", "commit push"]):
            return RiskLevel.HIGH_RISK
        if any(w in text_lower for w in ["edit", "write", "patch", "modify", "read email", "photos", "clipboard"]):
            return RiskLevel.SENSITIVE
        if any(w in text_lower for w in ["create folder", "draft", "navigate", "prepare post"]):
            return RiskLevel.LOW_RISK
        return RiskLevel.SAFE
