"""
SHIVANI Episodic Memory Manager
Maintains records of completed tasks, workflows, key outcomes, artifacts created,
and user feedback to enable recall of historical actions ("What did we do yesterday?").
"""

from typing import Any, Dict, List, Optional
from memory.models import MemoryCategory, MemoryItem, MemoryScope, MemorySource
from memory.storage.sqlite_store import SQLiteMemoryStore


class EpisodicMemory:
    def __init__(self, store: SQLiteMemoryStore):
        self.store = store

    def record_episode(
        self,
        task_id: str,
        query: str,
        summary: str,
        status: str,
        artifacts: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        explanation: Optional[str] = None,
    ) -> MemoryItem:
        """Records an execution episode with outcomes and artifacts."""
        payload = {
            "task_id": task_id,
            "query": query,
            "summary": summary,
            "status": status,
            "artifacts": artifacts or [],
            "project_id": project_id,
        }
        item = MemoryItem(
            category=MemoryCategory.TASK,
            scope=MemoryScope.PROJECT if project_id else MemoryScope.GLOBAL,
            scope_id=project_id,
            key=f"episode_{task_id}",
            value=payload,
            confidence=1.0,
            source=MemorySource.TASK_RESULT,
            metadata=metadata or {},
            explanation=explanation or f"Episodic record for task '{query}' ({status})",
        )
        return self.store.save(item)

    def get_recent_episodes(
        self,
        project_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """Retrieves recent task episodes."""
        return self.store.query(
            scope=MemoryScope.PROJECT if project_id else None,
            scope_id=project_id,
            category=MemoryCategory.TASK,
            limit=limit,
        )

    def find_episodes(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Searches past episodes by query text across summaries and metadata."""
        return self.store.search(
            query_text=query,
            category=MemoryCategory.TASK,
            limit=limit,
        )

    def get_episode_by_task(self, task_id: str) -> Optional[MemoryItem]:
        """Looks up an episode by task id."""
        return self.store.get_by_key(
            category=MemoryCategory.TASK,
            key=f"episode_{task_id}",
        )
