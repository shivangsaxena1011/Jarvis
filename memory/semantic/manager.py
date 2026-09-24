"""
SHIVANI Semantic Memory Manager
Stores long-term facts, project architectures, repository paths, framework conventions,
and persistent domain knowledge across scopes.
"""

from typing import Any, List, Optional
from memory.models import MemoryCategory, MemoryItem, MemoryScope, MemorySource
from memory.storage.sqlite_store import SQLiteMemoryStore


class SemanticMemory:
    def __init__(self, store: SQLiteMemoryStore):
        self.store = store

    def store_fact(
        self,
        key: str,
        value: Any,
        scope: MemoryScope = MemoryScope.GLOBAL,
        scope_id: Optional[str] = None,
        confidence: float = 1.0,
        source: MemorySource = MemorySource.EXPLICIT_USER,
        explanation: Optional[str] = None,
    ) -> MemoryItem:
        """Stores a persistent fact or knowledge snippet."""
        category = MemoryCategory.PROJECT if scope == MemoryScope.PROJECT else MemoryCategory.CONTEXT
        item = MemoryItem(
            category=category,
            scope=scope,
            scope_id=scope_id,
            key=key,
            value=value,
            confidence=confidence,
            source=source,
            explanation=explanation or f"Semantic knowledge recorded for '{key}'",
        )
        return self.store.save(item)

    def get_fact(
        self,
        key: str,
        scope: MemoryScope = MemoryScope.GLOBAL,
        scope_id: Optional[str] = None,
    ) -> Optional[Any]:
        """Retrieves a stored fact by key and scope."""
        category = MemoryCategory.PROJECT if scope == MemoryScope.PROJECT else MemoryCategory.CONTEXT
        item = self.store.get_by_key(
            category=category,
            key=key,
            scope=scope,
            scope_id=scope_id,
        )
        return item.value if item else None

    def search_facts(
        self,
        query: str,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """Searches facts matching query string."""
        return self.store.search(
            query_text=query,
            scope=scope,
            scope_id=scope_id,
            limit=limit,
        )

    def list_project_facts(self, project_id: str) -> List[MemoryItem]:
        """Retrieves all semantic facts associated with a project."""
        return self.store.query(
            scope=MemoryScope.PROJECT,
            scope_id=project_id,
            category=MemoryCategory.PROJECT,
        )
