"""
SHIVANI Unified Memory Manager
Orchestrates short-term working context, episodic history, semantic knowledge,
user preferences, and task checkpoints through a single coherent API.
Guarantees privacy, inspectability, and zero secret persistence.
"""

from datetime import timedelta
from typing import Any, Dict, List, Optional

from memory.models import (
    MemoryCategory,
    MemoryItem,
    MemoryScope,
    MemorySource,
    SecretRedactor,
    utc_now,
)
from memory.storage.sqlite_store import SQLiteMemoryStore
from memory.preferences.manager import PreferenceManager
from memory.short_term.manager import ShortTermMemory
from memory.episodic.manager import EpisodicMemory
from memory.semantic.manager import SemanticMemory
from memory.task_memory.manager import TaskMemory


class MemoryManager:
    def __init__(self, db_path: str = "data/memory.db", session_id: Optional[str] = None):
        self.store = SQLiteMemoryStore(db_path=db_path)
        self.preferences = PreferenceManager(self.store)
        self.short_term = ShortTermMemory(self.store, session_id=session_id)
        self.episodic = EpisodicMemory(self.store)
        self.semantic = SemanticMemory(self.store)
        self.task_memory = TaskMemory(self.store)

    def remember(
        self,
        key: str,
        value: Any,
        category: MemoryCategory = MemoryCategory.CONTEXT,
        scope: MemoryScope = MemoryScope.GLOBAL,
        scope_id: Optional[str] = None,
        confidence: float = 1.0,
        source: MemorySource = MemorySource.EXPLICIT_USER,
        explanation: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """Stores a memory item with confidence scoring and secret sanitization."""
        expires_at = utc_now() + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        item = MemoryItem(
            category=category,
            scope=scope,
            scope_id=scope_id,
            key=key,
            value=value,
            confidence=confidence,
            source=source,
            expires_at=expires_at,
            metadata=metadata or {},
            explanation=explanation or f"Stored memory for '{key}'",
        )
        return self.store.save(item)

    def recall(
        self,
        key: str,
        category: Optional[MemoryCategory] = None,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
    ) -> Optional[Any]:
        """Recalls the value for a given key, searching across categories if not specified."""
        cats_to_search = [category] if category else [
            MemoryCategory.USER_PREFERENCE,
            MemoryCategory.PROJECT,
            MemoryCategory.CONTEXT,
            MemoryCategory.TASK,
            MemoryCategory.DEVICE,
            MemoryCategory.SYSTEM_SETTING,
        ]
        for cat in cats_to_search:
            item = self.store.get_by_key(category=cat, key=key, scope=scope, scope_id=scope_id)
            if item:
                return item.value
        return None

    def get_preference(
        self,
        key: str,
        default: Any = None,
        project_id: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Any:
        """Resolves user preference taking into account device/project overrides."""
        return self.preferences.resolve_preference(
            key=key,
            project_id=project_id,
            device_id=device_id,
            default=default,
        )

    def set_preference(
        self,
        key: str,
        value: Any,
        scope: MemoryScope = MemoryScope.GLOBAL,
        scope_id: Optional[str] = None,
        explanation: Optional[str] = None,
    ) -> MemoryItem:
        """Sets a user preference with conflict resolution (latest explicit user value wins)."""
        return self.preferences.set_preference(
            key=key,
            value=value,
            scope=scope,
            scope_id=scope_id,
            explanation=explanation,
            source=MemorySource.EXPLICIT_USER,
        )

    def search(
        self,
        query: str,
        category: Optional[MemoryCategory] = None,
        scope: Optional[MemoryScope] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """Searches memories matching query text across keys, values, and explanations."""
        return self.store.search(
            query_text=query,
            category=category,
            scope=scope,
            limit=limit,
        )

    def forget(
        self,
        memory_id: Optional[str] = None,
        key: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
    ) -> bool:
        """Deletes a memory item either by direct ID or key+category."""
        if memory_id:
            return self.store.delete(memory_id)
        if key and category:
            return self.store.delete_by_key(category=category, key=key, scope=scope, scope_id=scope_id) > 0
        if key:
            # Delete across all categories
            count = 0
            for cat in MemoryCategory:
                count += self.store.delete_by_key(category=cat, key=key, scope=scope, scope_id=scope_id)
            return count > 0
        return False

    def explain(self, key_or_id: str) -> Optional[Dict[str, Any]]:
        """Answers: 'Why did you use that memory / where did it come from?'"""
        item = self.store.get_by_id(key_or_id)
        if not item:
            # Try by key
            for cat in MemoryCategory:
                item = self.store.get_by_key(category=cat, key=key_or_id)
                if item:
                    break
        if not item:
            return None

        return {
            "id": item.id,
            "key": item.key,
            "category": item.category.value,
            "scope": item.scope.value,
            "source": item.source.value,
            "confidence": item.confidence,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
            "explanation": item.explanation or "No explanation provided.",
        }

    def clear_scope(self, scope: MemoryScope, scope_id: Optional[str] = None) -> int:
        return self.store.clear_scope(scope=scope, scope_id=scope_id)

    def purge_expired(self) -> int:
        return self.store.purge_expired()

    def inspect_summary(self) -> Dict[str, Any]:
        """Provides an inspectable summary of stored memories without revealing sensitive values."""
        all_items = self.store.query(limit=500)
        summary: Dict[str, Any] = {
            "total_count": len(all_items),
            "by_category": {},
            "by_scope": {},
            "sample_keys": [it.key for it in all_items[:10]],
        }
        for it in all_items:
            cat = it.category.value
            scp = it.scope.value
            summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1
            summary["by_scope"][scp] = summary["by_scope"].get(scp, 0) + 1
        return summary
