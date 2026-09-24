"""
SHIVANI SQLite Memory Store
Provides thread-safe persistent storage with schema versioning,
indexed lookups, full-text keyword search, and automatic expiration purges.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional

from memory.models import MemoryCategory, MemoryItem, MemoryScope, MemorySource, utc_now


class SQLiteMemoryStore:
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    scope_id TEXT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT,
                    metadata TEXT,
                    explanation TEXT
                )
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_lookup 
                ON memories (scope, scope_id, category, key)
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_category 
                ON memories (category)
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_key 
                ON memories (key)
                """
            )

    def _row_to_item(self, row: sqlite3.Row) -> MemoryItem:
        expires_at = datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
        return MemoryItem(
            id=row["id"],
            category=MemoryCategory(row["category"]),
            scope=MemoryScope(row["scope"]),
            scope_id=row["scope_id"],
            key=row["key"],
            value=json.loads(row["value"]),
            confidence=float(row["confidence"]),
            source=MemorySource(row["source"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            expires_at=expires_at,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            explanation=row["explanation"],
        )

    def save(self, item: MemoryItem) -> MemoryItem:
        """Upserts a memory item. If an item with the same scope, scope_id, category, and key exists, it is updated."""
        with self._lock, self._conn:
            # Check for existing item with matching key and scope
            cursor = self._conn.execute(
                """
                SELECT id, created_at FROM memories 
                WHERE scope = ? AND (scope_id = ? OR (scope_id IS NULL AND ? IS NULL))
                  AND category = ? AND key = ?
                LIMIT 1
                """,
                (item.scope.value, item.scope_id, item.scope_id, item.category.value, item.key),
            )
            existing = cursor.fetchone()

            item.updated_at = utc_now()
            value_json = json.dumps(item.value)
            metadata_json = json.dumps(item.metadata)
            expires_str = item.expires_at.isoformat() if item.expires_at else None

            if existing:
                item.id = existing["id"]
                item.created_at = datetime.fromisoformat(existing["created_at"])
                self._conn.execute(
                    """
                    UPDATE memories SET
                        value = ?,
                        confidence = ?,
                        source = ?,
                        updated_at = ?,
                        expires_at = ?,
                        metadata = ?,
                        explanation = ?
                    WHERE id = ?
                    """,
                    (
                        value_json,
                        item.confidence,
                        item.source.value,
                        item.updated_at.isoformat(),
                        expires_str,
                        metadata_json,
                        item.explanation,
                        item.id,
                    ),
                )
            else:
                self._conn.execute(
                    """
                    INSERT INTO memories (
                        id, category, scope, scope_id, key, value, confidence,
                        source, created_at, updated_at, expires_at, metadata, explanation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.id,
                        item.category.value,
                        item.scope.value,
                        item.scope_id,
                        item.key,
                        value_json,
                        item.confidence,
                        item.source.value,
                        item.created_at.isoformat(),
                        item.updated_at.isoformat(),
                        expires_str,
                        metadata_json,
                        item.explanation,
                    ),
                )
        return item

    def get_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cur.fetchone()
            if not row:
                return None
            item = self._row_to_item(row)
            if item.is_expired():
                self.delete(memory_id)
                return None
            return item

    def get_by_key(
        self,
        category: MemoryCategory,
        key: str,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
    ) -> Optional[MemoryItem]:
        query = "SELECT * FROM memories WHERE category = ? AND key = ?"
        params: List[Any] = [category.value, key]
        if scope:
            query += " AND scope = ?"
            params.append(scope.value)
        if scope_id is not None:
            query += " AND scope_id = ?"
            params.append(scope_id)
        query += " ORDER BY updated_at DESC LIMIT 1"

        with self._lock:
            cur = self._conn.execute(query, tuple(params))
            row = cur.fetchone()
            if not row:
                return None
            item = self._row_to_item(row)
            if item.is_expired():
                self.delete(item.id)
                return None
            return item

    def query(
        self,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        key: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 50,
    ) -> List[MemoryItem]:
        conditions = ["confidence >= ?"]
        params: List[Any] = [min_confidence]

        if scope:
            conditions.append("scope = ?")
            params.append(scope.value)
        if scope_id is not None:
            conditions.append("scope_id = ?")
            params.append(scope_id)
        if category:
            conditions.append("category = ?")
            params.append(category.value)
        if key:
            conditions.append("key = ?")
            params.append(key)

        sql = f"SELECT * FROM memories WHERE {' AND '.join(conditions)} ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        results: List[MemoryItem] = []
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            for row in cur.fetchall():
                item = self._row_to_item(row)
                if not item.is_expired():
                    results.append(item)
                else:
                    self.delete(item.id)
        return results

    def search(
        self,
        query_text: str,
        category: Optional[MemoryCategory] = None,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[MemoryItem]:
        wildcard = f"%{query_text.lower()}%"
        conditions = [
            "(LOWER(key) LIKE ? OR LOWER(value) LIKE ? OR LOWER(COALESCE(explanation, '')) LIKE ? OR LOWER(COALESCE(metadata, '')) LIKE ?)"
        ]
        params: List[Any] = [wildcard, wildcard, wildcard, wildcard]

        if category:
            conditions.append("category = ?")
            params.append(category.value)
        if scope:
            conditions.append("scope = ?")
            params.append(scope.value)
        if scope_id is not None:
            conditions.append("scope_id = ?")
            params.append(scope_id)

        sql = f"SELECT * FROM memories WHERE {' AND '.join(conditions)} ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        results: List[MemoryItem] = []
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            for row in cur.fetchall():
                item = self._row_to_item(row)
                if not item.is_expired():
                    results.append(item)
                else:
                    self.delete(item.id)
        return results

    def delete(self, memory_id: str) -> bool:
        with self._lock, self._conn:
            cur = self._conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cur.rowcount > 0

    def delete_by_key(
        self,
        category: MemoryCategory,
        key: str,
        scope: Optional[MemoryScope] = None,
        scope_id: Optional[str] = None,
    ) -> int:
        conditions = ["category = ?", "key = ?"]
        params: List[Any] = [category.value, key]
        if scope:
            conditions.append("scope = ?")
            params.append(scope.value)
        if scope_id is not None:
            conditions.append("scope_id = ?")
            params.append(scope_id)

        sql = f"DELETE FROM memories WHERE {' AND '.join(conditions)}"
        with self._lock, self._conn:
            cur = self._conn.execute(sql, tuple(params))
            return cur.rowcount

    def purge_expired(self) -> int:
        now_str = utc_now().isoformat()
        with self._lock, self._conn:
            cur = self._conn.execute(
                "DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now_str,),
            )
            return cur.rowcount

    def clear_scope(self, scope: MemoryScope, scope_id: Optional[str] = None) -> int:
        conditions = ["scope = ?"]
        params: List[Any] = [scope.value]
        if scope_id is not None:
            conditions.append("scope_id = ?")
            params.append(scope_id)

        sql = f"DELETE FROM memories WHERE {' AND '.join(conditions)}"
        with self._lock, self._conn:
            cur = self._conn.execute(sql, tuple(params))
            return cur.rowcount

    def close(self) -> None:
        with self._lock:
            self._conn.close()
