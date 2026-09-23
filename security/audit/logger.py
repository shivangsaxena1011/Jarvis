"""
SHIVANI Structured Audit Logger
Records immutable structured task events, tool executions, and user decisions.
Automatically redacts API keys, credentials, and authentication tokens.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# Regex patterns for redacting sensitive values
SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|secret|token|password|auth|bearer)[\s:=]+['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?", r"\1: [REDACTED]"),
    (r"(?i)(AIza[0-9A-Za-z-_]{35})", "[REDACTED_GEMINI_KEY]"),
    (r"(?i)(sk-[a-zA-Z0-9]{20,})", "[REDACTED_OPENAI_KEY]"),
]


class AuditLogger:
    def __init__(self, log_path: str = "audit.jsonl"):
        self.log_path = Path(log_path)

    @classmethod
    def redact(cls, text: str) -> str:
        """Masks sensitive tokens from string representation."""
        if not text:
            return ""
        result = text
        for pattern, replacement in SECRET_PATTERNS:
            result = re.sub(pattern, replacement, result)
        return result

    @classmethod
    def redact_data(cls, data: Any) -> Any:
        """Recursively sanitizes dictionary, list, or string structures."""
        if isinstance(data, dict):
            clean = {}
            for k, v in data.items():
                if any(secret_kw in k.lower() for secret_kw in ("key", "secret", "password", "token", "auth")):
                    clean[k] = "[REDACTED]"
                else:
                    clean[k] = cls.redact_data(v)
            return clean
        elif isinstance(data, list):
            return [cls.redact_data(item) for item in data]
        elif isinstance(data, str):
            return cls.redact(data)
        return data

    def log_event(
        self,
        event_type: str,
        task_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Appends a structured event record to the audit file."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "task_id": task_id,
            "tool_name": tool_name,
            "details": self.redact_data(details or {}),
            "success": success,
            "error": self.redact(error) if error else None
        }

        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            # Fallback print if file cannot be written
            print(f"[AUDIT ERROR] Failed to write audit log: {e}")

        return record

    def get_recent_events(self, limit: int = 50) -> list[Dict[str, Any]]:
        """Reads the latest events from the audit log."""
        if not self.log_path.exists():
            return []
        
        events = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except Exception:
            pass
        return events
