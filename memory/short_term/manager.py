"""
SHIVANI Short-Term Working Memory
Manages ephemeral conversational dialog, active UI state, and session-scoped context
with configurable TTL and automatic expiration purge.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid

from memory.models import MemoryCategory, MemoryItem, MemoryScope, MemorySource, utc_now
from memory.storage.sqlite_store import SQLiteMemoryStore


class ShortTermMemory:
    def __init__(self, store: SQLiteMemoryStore, session_id: Optional[str] = None):
        self.store = store
        self.session_id = session_id or str(uuid.uuid4())
        self._counter = 0

    def add_turn(self, role: str, content: str, ttl_seconds: int = 7200) -> MemoryItem:
        """Appends a conversation turn to short-term memory."""
        self._counter += 1
        turn_id = f"turn_{self._counter:06d}_{int(utc_now().timestamp() * 1000)}"
        expires_at = utc_now() + timedelta(seconds=ttl_seconds)
        item = MemoryItem(
            category=MemoryCategory.CONTEXT,
            scope=MemoryScope.SESSION,
            scope_id=self.session_id,
            key=turn_id,
            value={"role": role, "content": content, "turn_index": self._counter},
            confidence=1.0,
            source=MemorySource.EXPLICIT_USER if role == "user" else MemorySource.SYSTEM,
            expires_at=expires_at,
            metadata={"turn_index": self._counter},
            explanation=f"Conversational turn by {role}",
        )
        return self.store.save(item)

    def get_recent_turns(self, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieves recent conversation turns in chronological order."""
        items = self.store.query(
            scope=MemoryScope.SESSION,
            scope_id=self.session_id,
            category=MemoryCategory.CONTEXT,
            limit=limit,
        )
        # Sort chronologically by turn_index or created_at
        sorted_items = sorted(
            items,
            key=lambda it: it.metadata.get("turn_index", 0) if it.metadata else 0,
        )
        turns = []
        for it in sorted_items:
            if isinstance(it.value, dict) and "role" in it.value and "content" in it.value:
                turns.append({"role": it.value["role"], "content": it.value["content"]})
        return turns

    def set_working_context(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
        explanation: Optional[str] = None,
    ) -> MemoryItem:
        """Sets a temporary working variable (e.g. active_app, selected_text, target_url)."""
        expires_at = utc_now() + timedelta(seconds=ttl_seconds)
        item = MemoryItem(
            category=MemoryCategory.CONTEXT,
            scope=MemoryScope.SESSION,
            scope_id=self.session_id,
            key=key,
            value=value,
            confidence=1.0,
            source=MemorySource.SYSTEM,
            expires_at=expires_at,
            explanation=explanation or f"Working session variable for {key}",
        )
        return self.store.save(item)

    def get_working_context(self, key: str) -> Optional[Any]:
        """Retrieves a working session context variable."""
        item = self.store.get_by_key(
            category=MemoryCategory.CONTEXT,
            key=key,
            scope=MemoryScope.SESSION,
            scope_id=self.session_id,
        )
        return item.value if item else None

    def clear_session(self) -> int:
        """Wipes all short-term context for the current session."""
        return self.store.clear_scope(MemoryScope.SESSION, scope_id=self.session_id)
