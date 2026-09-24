"""
SHIVANI Persistent Automation Store (Phase 15).
SQLite-backed persistence for Automations, Execution Runs, Versions, and Idempotency Keys.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Union

from core.automation.models import Automation, AutomationRun, AutomationStatus, RunStatus


class AutomationStore:
    """Thread-safe SQLite storage for automations and run history."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            base = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "Shivani" / "data"
            base.mkdir(parents=True, exist_ok=True)
            self.db_path = base / "automations.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                # 1. Automations Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS automations (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        version INTEGER NOT NULL DEFAULT 1,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        owner TEXT NOT NULL DEFAULT 'user',
                        scope TEXT NOT NULL DEFAULT 'GLOBAL',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_run TEXT,
                        next_run TEXT,
                        data JSON NOT NULL
                    )
                """)
                # 2. Automation Runs History Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS automation_runs (
                        id TEXT PRIMARY KEY,
                        automation_id TEXT NOT NULL,
                        automation_name TEXT NOT NULL,
                        started_at TEXT NOT NULL,
                        completed_at TEXT,
                        status TEXT NOT NULL,
                        data JSON NOT NULL,
                        FOREIGN KEY (automation_id) REFERENCES automations(id) ON DELETE CASCADE
                    )
                """)
                # 3. Automation Versions History
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS automation_versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        automation_id TEXT NOT NULL,
                        version INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        data JSON NOT NULL
                    )
                """)
                # 4. Idempotency Records
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS idempotency_records (
                        idempotency_key TEXT PRIMARY KEY,
                        automation_id TEXT NOT NULL,
                        step_id TEXT,
                        hash_value TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        result JSON
                    )
                """)
                conn.commit()
            finally:
                conn.close()

    # ==========================================================================
    # Automation CRUD & Versioning
    # ==========================================================================

    def save_automation(self, automation: Automation) -> Automation:
        automation.updated_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO automations (id, name, status, version, enabled, owner, scope, created_at, updated_at, last_run, next_run, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        status = excluded.status,
                        version = excluded.version,
                        enabled = excluded.enabled,
                        owner = excluded.owner,
                        scope = excluded.scope,
                        updated_at = excluded.updated_at,
                        last_run = excluded.last_run,
                        next_run = excluded.next_run,
                        data = excluded.data
                    """,
                    (
                        automation.id,
                        automation.name,
                        automation.status.value,
                        automation.version,
                        1 if automation.enabled else 0,
                        automation.owner,
                        automation.scope.value,
                        automation.created_at,
                        automation.updated_at,
                        automation.last_run,
                        automation.next_run,
                        automation.model_dump_json(),
                    ),
                )
                # Record version snapshot
                cursor.execute(
                    "INSERT INTO automation_versions (automation_id, version, created_at, data) VALUES (?, ?, ?, ?)",
                    (automation.id, automation.version, automation.updated_at, automation.model_dump_json()),
                )
                conn.commit()
                return automation
            finally:
                conn.close()

    def get_automation(self, automation_id: str) -> Optional[Automation]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT data FROM automations WHERE id = ?", (automation_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return Automation.model_validate_json(row["data"])
            finally:
                conn.close()

    def list_automations(self, status: Optional[AutomationStatus] = None) -> List[Automation]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if status:
                    cursor.execute("SELECT data FROM automations WHERE status = ? ORDER BY created_at DESC", (status.value,))
                else:
                    cursor.execute("SELECT data FROM automations ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [Automation.model_validate_json(r["data"]) for r in rows]
            finally:
                conn.close()

    def delete_automation(self, automation_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM automations WHERE id = ?", (automation_id,))
                cursor.execute("DELETE FROM automation_versions WHERE automation_id = ?", (automation_id,))
                cursor.execute("DELETE FROM automation_runs WHERE automation_id = ?", (automation_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()

    def get_versions(self, automation_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT version, created_at, data FROM automation_versions WHERE automation_id = ? ORDER BY version DESC", (automation_id,))
                rows = cursor.fetchall()
                return [{"version": r["version"], "created_at": r["created_at"], "data": json.loads(r["data"])} for r in rows]
            finally:
                conn.close()

    # ==========================================================================
    # Automation Run History
    # ==========================================================================

    def record_run(self, run: AutomationRun) -> AutomationRun:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO automation_runs (id, automation_id, automation_name, started_at, completed_at, status, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        completed_at = excluded.completed_at,
                        status = excluded.status,
                        data = excluded.data
                    """,
                    (
                        run.id,
                        run.automation_id,
                        run.automation_name,
                        run.started_at,
                        run.completed_at,
                        run.status.value,
                        run.model_dump_json(),
                    ),
                )
                conn.commit()
                return run
            finally:
                conn.close()

    def get_run(self, run_id: str) -> Optional[AutomationRun]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT data FROM automation_runs WHERE id = ?", (run_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return AutomationRun.model_validate_json(row["data"])
            finally:
                conn.close()

    def list_runs(self, automation_id: Optional[str] = None, limit: int = 50) -> List[AutomationRun]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                if automation_id:
                    cursor.execute("SELECT data FROM automation_runs WHERE automation_id = ? ORDER BY started_at DESC LIMIT ?", (automation_id, limit))
                else:
                    cursor.execute("SELECT data FROM automation_runs ORDER BY started_at DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [AutomationRun.model_validate_json(r["data"]) for r in rows]
            finally:
                conn.close()

    # ==========================================================================
    # Idempotency Records
    # ==========================================================================

    def check_and_set_idempotency(self, key: str, automation_id: str, step_id: str, hash_val: str, result: Optional[Any] = None) -> bool:
        """Returns True if record already exists (duplicate action detected!)."""
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT hash_value FROM idempotency_records WHERE idempotency_key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    return True
                cursor.execute(
                    "INSERT INTO idempotency_records (idempotency_key, automation_id, step_id, hash_value, created_at, result) VALUES (?, ?, ?, ?, ?, ?)",
                    (key, automation_id, step_id, hash_val, datetime.now(timezone.utc).isoformat(), json.dumps(result) if result else None),
                )
                conn.commit()
                return False
            finally:
                conn.close()
