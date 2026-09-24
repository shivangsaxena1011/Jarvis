"""
SHIVANI Idempotency System
Guarantees that external side-effect operations (sending emails, publishing social posts,
creating GitHub issues, git commits/pushes, phone commands) are never duplicated.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field



class ExecutionState(str, Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    VERIFIED = "VERIFIED"


class IdempotentRecord(BaseModel):
    operation_id: str
    idempotency_key: str
    action_type: str
    payload_hash: str
    state: ExecutionState = ExecutionState.PENDING
    result_data: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def result(self) -> Optional[Dict[str, Any]]:
        return self.result_data


class IdempotencyManager:
    def __init__(self):
        self._records: Dict[str, IdempotentRecord] = {}
        self._lock = threading.Lock()

    @classmethod
    def compute_key(cls, action_type: str, payload: Dict[str, Any], scope: str = "global") -> str:
        serialized = json.dumps(payload, sort_keys=True)
        h = hashlib.sha256(f"{action_type}:{scope}:{serialized}".encode("utf-8")).hexdigest()
        return f"{action_type}_{h[:16]}"

    def check_or_register(
        self,
        action_type: str,
        payload: Dict[str, Any],
        operation_id: Optional[str] = None,
        initial_state: ExecutionState = ExecutionState.PENDING,
    ) -> Tuple[bool, IdempotentRecord]:
        """
        Returns (is_duplicate, record).
        If is_duplicate is True, the side-effect was already executed or is currently executing!
        """
        key = self.compute_key(action_type, payload)
        with self._lock:
            if key in self._records:
                rec = self._records[key]
                if rec.state in (ExecutionState.COMPLETED, ExecutionState.VERIFIED):
                    return True, rec
                elif rec.state == ExecutionState.EXECUTING:
                    return True, rec

            serialized = json.dumps(payload, sort_keys=True)
            p_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            op_id = operation_id or f"op_{int(datetime.now(timezone.utc).timestamp()*1000)}"

            new_rec = IdempotentRecord(
                operation_id=op_id,
                idempotency_key=key,
                action_type=action_type,
                payload_hash=p_hash,
                state=initial_state,
            )
            self._records[key] = new_rec
            return False, new_rec

    def record_result(self, operation_id_or_key: str, result: Dict[str, Any], state: ExecutionState = ExecutionState.COMPLETED) -> None:
        with self._lock:
            for rec in self._records.values():
                if rec.operation_id == operation_id_or_key or rec.idempotency_key == operation_id_or_key:
                    rec.state = state
                    rec.result_data = result
                    rec.updated_at = datetime.now(timezone.utc).isoformat()
                    return
            if operation_id_or_key in self._records:
                rec = self._records[operation_id_or_key]
                rec.state = state
                rec.result_data = result
                rec.updated_at = datetime.now(timezone.utc).isoformat()


    def mark_completed(self, idempotency_key: str, result_data: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            rec = self._records.get(idempotency_key)
            if rec:
                rec.state = ExecutionState.COMPLETED
                rec.result_data = result_data
                rec.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_verified(self, idempotency_key: str) -> None:
        with self._lock:
            rec = self._records.get(idempotency_key)
            if rec:
                rec.state = ExecutionState.VERIFIED
                rec.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self, idempotency_key: str) -> None:
        with self._lock:
            rec = self._records.get(idempotency_key)
            if rec:
                rec.state = ExecutionState.FAILED
                rec.updated_at = datetime.now(timezone.utc).isoformat()
