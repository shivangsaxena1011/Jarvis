"""
SHIVANI Preferences Manager
Handles explicit and inferred user preferences across GLOBAL, PROJECT, and DEVICE scopes,
implementing conflict resolution where the latest explicit preference strictly takes precedence.
"""

from typing import Any, List, Optional
from memory.models import MemoryCategory, MemoryItem, MemoryScope, MemorySource
from memory.storage.sqlite_store import SQLiteMemoryStore


class PreferenceManager:
    def __init__(self, store: SQLiteMemoryStore):
        self.store = store

    def set_preference(
        self,
        key: str,
        value: Any,
        scope: MemoryScope = MemoryScope.GLOBAL,
        scope_id: Optional[str] = None,
        confidence: float = 1.0,
        explanation: Optional[str] = None,
        source: MemorySource = MemorySource.EXPLICIT_USER,
    ) -> MemoryItem:
        """Sets a user preference. Overwrites existing matching preference in the given scope."""
        item = MemoryItem(
            category=MemoryCategory.USER_PREFERENCE,
            scope=scope,
            scope_id=scope_id,
            key=key,
            value=value,
            confidence=confidence,
            source=source,
            explanation=explanation or f"User preference configured for {key}",
        )
        return self.store.save(item)

    def get_preference(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.GLOBAL,
        scope_id: Optional[str] = None,
        fallback_global: bool = True,
    ) -> Optional[Any]:
        """Retrieves a preference value, falling back to global scope if not found in specific scope."""
        item = self.store.get_by_key(
            category=MemoryCategory.USER_PREFERENCE,
            key=key,
            scope=scope,
            scope_id=scope_id,
        )
        if item:
            return item.value

        if fallback_global and scope != MemoryScope.GLOBAL:
            global_item = self.store.get_by_key(
                category=MemoryCategory.USER_PREFERENCE,
                key=key,
                scope=MemoryScope.GLOBAL,
            )
            if global_item:
                return global_item.value

        return None

    def resolve_preference(
        self,
        key: str,
        project_id: Optional[str] = None,
        device_id: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        Resolves preference with hierarchy:
        1. Specific Device preference
        2. Specific Project preference
        3. Global preference
        4. Default value
        """
        if device_id:
            val = self.get_preference(key, scope=MemoryScope.DEVICE, scope_id=device_id, fallback_global=False)
            if val is not None:
                return val

        if project_id:
            val = self.get_preference(key, scope=MemoryScope.PROJECT, scope_id=project_id, fallback_global=False)
            if val is not None:
                return val

        val = self.get_preference(key, scope=MemoryScope.GLOBAL, fallback_global=False)
        if val is not None:
            return val

        return default

    def list_preferences(
        self,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
    ) -> List[MemoryItem]:
        return self.store.query(
            scope=scope,
            scope_id=scope_id,
            category=MemoryCategory.USER_PREFERENCE,
        )

    def delete_preference(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.GLOBAL,
        scope_id: Optional[str] = None,
    ) -> bool:
        count = self.store.delete_by_key(
            category=MemoryCategory.USER_PREFERENCE,
            key=key,
            scope=scope,
            scope_id=scope_id,
        )
        return count > 0
