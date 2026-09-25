"""Persistent Trust Store for Phase 18: Cross-Device Continuity.

Uses SQLite in WAL mode with connection pooling and thread safety to persist
device identities, trust states, permissions, active pairing sessions, handoffs,
and chunked file transfer records.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from core.devices.models import (
    ConnectionState,
    Device,
    DeviceTrustState,
    FileTransferSession,
    HandoffStatus,
    HandoffType,
    PairingSession,
    TaskHandoff,
    TransferStatus,
)

logger = logging.getLogger("shivani.devices.trust_store")


class TrustStore:
    """SQLite-backed persistent store for device mesh identities and trust states."""

    def __init__(self, db_path: str = "data/devices.db"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._init_db()

    @contextmanager
    def _get_connection(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS devices (
                        device_id TEXT PRIMARY KEY,
                        display_name TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        version TEXT NOT NULL,
                        capabilities TEXT NOT NULL,
                        trust_state TEXT NOT NULL,
                        connection_state TEXT NOT NULL,
                        permissions TEXT NOT NULL,
                        battery_level INTEGER,
                        is_charging INTEGER NOT NULL DEFAULT 0,
                        public_key TEXT,
                        auth_token TEXT,
                        ip_address TEXT,
                        port INTEGER NOT NULL DEFAULT 8765,
                        last_seen REAL NOT NULL,
                        metadata TEXT NOT NULL
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pairing_sessions (
                        session_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        display_name TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        code TEXT NOT NULL,
                        public_key TEXT,
                        created_at REAL NOT NULL,
                        expires_at REAL NOT NULL,
                        verified INTEGER NOT NULL DEFAULT 0,
                        metadata TEXT NOT NULL
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS handoffs (
                        handoff_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        source_device_id TEXT NOT NULL,
                        target_device_id TEXT NOT NULL,
                        handoff_type TEXT NOT NULL,
                        context_payload TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        expires_at REAL NOT NULL,
                        result_payload TEXT,
                        error_message TEXT
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS file_transfers (
                        session_id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        source_device_id TEXT NOT NULL,
                        target_device_id TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        bytes_transferred INTEGER NOT NULL DEFAULT 0,
                        chunk_size INTEGER NOT NULL,
                        total_chunks INTEGER NOT NULL,
                        chunks_received TEXT NOT NULL,
                        sha256_checksum TEXT,
                        status TEXT NOT NULL,
                        local_path TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        error_message TEXT
                    );
                    """
                )
                conn.commit()

    # -------------------------------------------------------------------------
    # Device CRUD & Trust State
    # -------------------------------------------------------------------------

    def upsert_device(self, device: Device) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO devices (
                        device_id, display_name, platform, version, capabilities,
                        trust_state, connection_state, permissions, battery_level,
                        is_charging, public_key, auth_token, ip_address, port,
                        last_seen, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(device_id) DO UPDATE SET
                        display_name=excluded.display_name,
                        platform=excluded.platform,
                        version=excluded.version,
                        capabilities=excluded.capabilities,
                        trust_state=excluded.trust_state,
                        connection_state=excluded.connection_state,
                        permissions=excluded.permissions,
                        battery_level=excluded.battery_level,
                        is_charging=excluded.is_charging,
                        public_key=coalesce(excluded.public_key, devices.public_key),
                        auth_token=coalesce(excluded.auth_token, devices.auth_token),
                        ip_address=excluded.ip_address,
                        port=excluded.port,
                        last_seen=excluded.last_seen,
                        metadata=excluded.metadata;
                    """,
                    (
                        device.device_id,
                        device.display_name,
                        device.platform,
                        device.version,
                        json.dumps(device.capabilities),
                        device.trust_state.value if isinstance(device.trust_state, DeviceTrustState) else device.trust_state,
                        device.connection_state.value if isinstance(device.connection_state, ConnectionState) else device.connection_state,
                        json.dumps(device.permissions),
                        device.battery_level,
                        1 if device.is_charging else 0,
                        device.public_key,
                        device.auth_token,
                        device.ip_address,
                        device.port,
                        device.last_seen,
                        json.dumps(device.metadata),
                    ),
                )
                conn.commit()

    def get_device(self, device_id: str) -> Optional[Device]:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return self._row_to_device(row)

    def list_devices(self, trust_state: Optional[DeviceTrustState] = None) -> List[Device]:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if trust_state:
                    state_val = trust_state.value if isinstance(trust_state, DeviceTrustState) else trust_state
                    cursor.execute("SELECT * FROM devices WHERE trust_state = ? ORDER BY last_seen DESC", (state_val,))
                else:
                    cursor.execute("SELECT * FROM devices ORDER BY last_seen DESC")
                rows = cursor.fetchall()
                return [self._row_to_device(r) for r in rows]

    def update_trust_state(self, device_id: str, new_state: DeviceTrustState) -> bool:
        state_val = new_state.value if isinstance(new_state, DeviceTrustState) else new_state
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE devices SET trust_state = ?, last_seen = ? WHERE device_id = ?",
                    (state_val, time.time(), device_id),
                )
                conn.commit()
                return cursor.rowcount > 0

    def update_permissions(self, device_id: str, permissions: List[str]) -> bool:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE devices SET permissions = ?, last_seen = ? WHERE device_id = ?",
                    (json.dumps(permissions), time.time(), device_id),
                )
                conn.commit()
                return cursor.rowcount > 0

    def revoke_device(self, device_id: str) -> bool:
        return self.update_trust_state(device_id, DeviceTrustState.REVOKED)

    def block_device(self, device_id: str) -> bool:
        return self.update_trust_state(device_id, DeviceTrustState.BLOCKED)

    def delete_device(self, device_id: str) -> bool:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM devices WHERE device_id = ?", (device_id,))
                conn.commit()
                return cursor.rowcount > 0

    def _row_to_device(self, row: sqlite3.Row) -> Device:
        return Device(
            device_id=row["device_id"],
            display_name=row["display_name"],
            platform=row["platform"],
            version=row["version"],
            capabilities=json.loads(row["capabilities"]),
            trust_state=DeviceTrustState(row["trust_state"]),
            connection_state=ConnectionState(row["connection_state"]),
            permissions=json.loads(row["permissions"]),
            battery_level=row["battery_level"],
            is_charging=bool(row["is_charging"]),
            public_key=row["public_key"],
            auth_token=row["auth_token"],
            ip_address=row["ip_address"],
            port=row["port"],
            last_seen=row["last_seen"],
            metadata=json.loads(row["metadata"]),
        )

    # -------------------------------------------------------------------------
    # Pairing Sessions
    # -------------------------------------------------------------------------

    def save_pairing_session(self, session: PairingSession) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO pairing_sessions (
                        session_id, device_id, display_name, platform, code,
                        public_key, created_at, expires_at, verified, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        verified=excluded.verified,
                        metadata=excluded.metadata;
                    """,
                    (
                        session.session_id,
                        session.device_id,
                        session.display_name,
                        session.platform,
                        session.code,
                        session.public_key,
                        session.created_at,
                        session.expires_at,
                        1 if session.verified else 0,
                        json.dumps(session.metadata),
                    ),
                )
                conn.commit()

    def get_pairing_session(self, session_id: str) -> Optional[PairingSession]:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM pairing_sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return PairingSession(
                    session_id=row["session_id"],
                    device_id=row["device_id"],
                    display_name=row["display_name"],
                    platform=row["platform"],
                    code=row["code"],
                    public_key=row["public_key"],
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                    verified=bool(row["verified"]),
                    metadata=json.loads(row["metadata"]),
                )

    def delete_pairing_session(self, session_id: str) -> bool:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM pairing_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return cursor.rowcount > 0

    # -------------------------------------------------------------------------
    # Handoffs
    # -------------------------------------------------------------------------

    def save_handoff(self, handoff: TaskHandoff) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO handoffs (
                        handoff_id, task_id, title, source_device_id, target_device_id,
                        handoff_type, context_payload, status, created_at, expires_at,
                        result_payload, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(handoff_id) DO UPDATE SET
                        status=excluded.status,
                        result_payload=excluded.result_payload,
                        error_message=excluded.error_message;
                    """,
                    (
                        handoff.handoff_id,
                        handoff.task_id,
                        handoff.title,
                        handoff.source_device_id,
                        handoff.target_device_id,
                        handoff.handoff_type.value if isinstance(handoff.handoff_type, HandoffType) else handoff.handoff_type,
                        json.dumps(handoff.context_payload),
                        handoff.status.value if isinstance(handoff.status, HandoffStatus) else handoff.status,
                        handoff.created_at,
                        handoff.expires_at,
                        json.dumps(handoff.result_payload) if handoff.result_payload else None,
                        handoff.error_message,
                    ),
                )
                conn.commit()

    def get_handoff(self, handoff_id: str) -> Optional[TaskHandoff]:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM handoffs WHERE handoff_id = ?", (handoff_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return self._row_to_handoff(row)

    def list_handoffs(self, target_device_id: Optional[str] = None) -> List[TaskHandoff]:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if target_device_id:
                    cursor.execute("SELECT * FROM handoffs WHERE target_device_id = ? ORDER BY created_at DESC", (target_device_id,))
                else:
                    cursor.execute("SELECT * FROM handoffs ORDER BY created_at DESC")
                return [self._row_to_handoff(r) for r in cursor.fetchall()]

    def update_handoff_status(
        self,
        handoff_id: str,
        status: HandoffStatus,
        result_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        status_val = status.value if isinstance(status, HandoffStatus) else status
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE handoffs
                    SET status = ?, result_payload = ?, error_message = ?
                    WHERE handoff_id = ?
                    """,
                    (
                        status_val,
                        json.dumps(result_payload) if result_payload else None,
                        error_message,
                        handoff_id,
                    ),
                )
                conn.commit()
                return cursor.rowcount > 0

    def _row_to_handoff(self, row: sqlite3.Row) -> TaskHandoff:
        return TaskHandoff(
            handoff_id=row["handoff_id"],
            task_id=row["task_id"],
            title=row["title"],
            source_device_id=row["source_device_id"],
            target_device_id=row["target_device_id"],
            handoff_type=HandoffType(row["handoff_type"]),
            context_payload=json.loads(row["context_payload"]),
            status=HandoffStatus(row["status"]),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            result_payload=json.loads(row["result_payload"]) if row["result_payload"] else None,
            error_message=row["error_message"],
        )

    # -------------------------------------------------------------------------
    # Chunked File Transfer Sessions
    # -------------------------------------------------------------------------

    def save_file_transfer(self, transfer: FileTransferSession) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO file_transfers (
                        session_id, filename, source_device_id, target_device_id,
                        file_size, bytes_transferred, chunk_size, total_chunks,
                        chunks_received, sha256_checksum, status, local_path,
                        created_at, updated_at, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        bytes_transferred=excluded.bytes_transferred,
                        chunks_received=excluded.chunks_received,
                        status=excluded.status,
                        updated_at=excluded.updated_at,
                        local_path=coalesce(excluded.local_path, file_transfers.local_path),
                        error_message=excluded.error_message;
                    """,
                    (
                        transfer.session_id,
                        transfer.filename,
                        transfer.source_device_id,
                        transfer.target_device_id,
                        transfer.file_size,
                        transfer.bytes_transferred,
                        transfer.chunk_size,
                        transfer.total_chunks,
                        json.dumps(transfer.chunks_received),
                        transfer.sha256_checksum,
                        transfer.status.value if isinstance(transfer.status, TransferStatus) else transfer.status,
                        transfer.local_path,
                        transfer.created_at,
                        time.time(),
                        transfer.error_message,
                    ),
                )
                conn.commit()

    def get_file_transfer(self, session_id: str) -> Optional[FileTransferSession]:
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM file_transfers WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return FileTransferSession(
                    session_id=row["session_id"],
                    filename=row["filename"],
                    source_device_id=row["source_device_id"],
                    target_device_id=row["target_device_id"],
                    file_size=row["file_size"],
                    bytes_transferred=row["bytes_transferred"],
                    chunk_size=row["chunk_size"],
                    total_chunks=row["total_chunks"],
                    chunks_received=json.loads(row["chunks_received"]),
                    sha256_checksum=row["sha256_checksum"] or "",
                    status=TransferStatus(row["status"]),
                    local_path=row["local_path"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    error_message=row["error_message"],
                )
