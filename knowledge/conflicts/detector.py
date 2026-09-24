"""
SHIVANI Knowledge Conflict & Contradiction Detector
Identifies factual contradictions between documents (e.g., outdated vs. current specs)
and registers conflict records for user review or automatic resolution.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Tuple

from knowledge.models import ConflictResolution, KnowledgeConflict, KnowledgeItem
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


class ConflictDetector:
    """Detects and resolves contradictory knowledge claims."""

    CONFLICT_PATTERNS = [
        ("Database Engine", re.compile(r"(?:database|db|datastore)\s*[:=]\s*([a-zA-Z0-9_\-]+)", re.IGNORECASE)),
        ("Python Version", re.compile(r"python\s*(?:version)?\s*[:=]?\s*([3]\.[0-9]{1,2})", re.IGNORECASE)),
        ("Server Port", re.compile(r"port\s*[:=]\s*([0-9]{2,5})", re.IGNORECASE)),
        ("Auth Mechanism", re.compile(r"(?:auth|authentication)\s*[:=]\s*([a-zA-Z0-9_\-]+)", re.IGNORECASE)),
        ("Primary Framework", re.compile(r"(?:framework|web framework)\s*[:=]\s*([a-zA-Z0-9_\-]+)", re.IGNORECASE)),
    ]

    def __init__(self, store: SQLiteKnowledgeStore):
        self.store = store

    def detect_conflicts_between_items(
        self,
        item_a: KnowledgeItem,
        item_b: KnowledgeItem,
    ) -> List[KnowledgeConflict]:
        """Compares two knowledge items and detects conflicting specifications."""
        conflicts: List[KnowledgeConflict] = []
        if item_a.id == item_b.id:
            return []

        for topic, pattern in self.CONFLICT_PATTERNS:
            m_a = pattern.search(item_a.content)
            m_b = pattern.search(item_b.content)

            if m_a and m_b:
                val_a = m_a.group(1).lower().strip()
                val_b = m_b.group(1).lower().strip()

                if val_a != val_b:
                    conflict = KnowledgeConflict(
                        topic=topic,
                        item_a_id=item_a.id,
                        item_b_id=item_b.id,
                        statement_a=f"{topic}: {val_a} (in '{item_a.title}')",
                        statement_b=f"{topic}: {val_b} (in '{item_b.title}')",
                        source_a=item_a.source or item_a.title,
                        source_b=item_b.source or item_b.title,
                        timestamp_a=item_a.updated_at,
                        timestamp_b=item_b.updated_at,
                        resolution_status=ConflictResolution.UNRESOLVED,
                    )
                    self.store.save_conflict(conflict)
                    conflicts.append(conflict)

        return conflicts

    def scan_all_conflicts(self, project_id: Optional[str] = None) -> List[KnowledgeConflict]:
        """Scans all pairs of items for conflicts."""
        items = self.store.list_items(project_id=project_id, limit=200)
        found: List[KnowledgeConflict] = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                detected = self.detect_conflicts_between_items(items[i], items[j])
                found.extend(detected)
        return found

    def resolve_by_recency(self, conflict: KnowledgeConflict) -> ConflictResolution:
        """Resolves conflict in favor of the newer document."""
        if conflict.timestamp_a >= conflict.timestamp_b:
            res = ConflictResolution.A_SUPERSEDES_B
            note = f"Resolved automatically: {conflict.source_a} is newer."
        else:
            res = ConflictResolution.B_SUPERSEDES_A
            note = f"Resolved automatically: {conflict.source_b} is newer."

        self.store.resolve_conflict(conflict.id, res, note)
        conflict.resolution_status = res
        conflict.resolution_note = note
        return res
