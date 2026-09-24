"""
SHIVANI High-Performance Structured Audit Logger
Records immutable JSONL event streams with log rotation and zero secret persistence.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional
from security.audit.logger import AuditLogger as BaseAuditLogger


class StructuredAuditLogger(BaseAuditLogger):
    def __init__(self, log_path: str = "logs/audit.jsonl", max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        super().__init__(log_path=log_path)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._lock = threading.Lock()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _rotate_if_needed(self) -> None:
        if not self.log_path.exists():
            return
        try:
            if self.log_path.stat().st_size >= self.max_bytes:
                for i in range(self.backup_count - 1, 0, -1):
                    sfn = self.log_path.with_name(f"{self.log_path.stem}.{i}{self.log_path.suffix}")
                    dfn = self.log_path.with_name(f"{self.log_path.stem}.{i+1}{self.log_path.suffix}")
                    if sfn.exists():
                        sfn.rename(dfn)
                dfn = self.log_path.with_name(f"{self.log_path.stem}.1{self.log_path.suffix}")
                self.log_path.rename(dfn)
        except Exception:
            pass

    def log_event(
        self,
        event_type: str,
        task_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
        component: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            self._rotate_if_needed()
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR" if not success else "INFO",
                "component": component or ("tool" if tool_name else "core"),
                "event": event_type,
                "task_id": task_id,
                "tool_name": tool_name,
                "success": success,
                "duration_ms": duration_ms,
                "details": self.redact_data(details) if details else {},
                "error": self.redact(error) if error else None,
            }
            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception:
                pass
            return entry

    def read_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.log_path.exists():
            return []
        with self._lock:
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                return [json.loads(line) for line in reversed(lines[-limit:])]
            except Exception:
                return []

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.read_recent_events(limit=limit)



# Re-export AuditLogger alias
AuditLogger = StructuredAuditLogger
AUDIT_LOGGER = StructuredAuditLogger()

