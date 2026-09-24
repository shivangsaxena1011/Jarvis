"""
SHIVANI SQLite Knowledge Store
Provides high-performance, thread-safe, transactional storage for knowledge items,
structured chunks, AST symbols, directed graph edges, and contradiction records.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Tuple

from knowledge.embeddings.provider import cosine_similarity
from knowledge.models import (
    CodeSymbol,
    CodeSymbolType,
    ConflictResolution,
    GraphEdge,
    KnowledgeChunk,
    KnowledgeConflict,
    KnowledgeItem,
    KnowledgeType,
    Provenance,
    RelationType,
    utc_now,
)


class SQLiteKnowledgeStore:
    """Thread-safe SQLite storage engine for SHIVANI Knowledge OS."""

    def __init__(self, db_path: str = "data/knowledge.db"):
        self.db_path = db_path
        self._lock = threading.Lock()

        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        if db_path != ":memory:":
            try:
                self._conn.execute("PRAGMA journal_mode = WAL;")
            except Exception:
                pass
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS knowledge_items (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT,
                    source TEXT,
                    project_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    permissions_tier TEXT NOT NULL DEFAULT 'internal',
                    provenance TEXT,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER NOT NULL DEFAULT 0,
                    chunk_index INTEGER NOT NULL DEFAULT 0,
                    heading_hierarchy TEXT,
                    line_start INTEGER NOT NULL DEFAULT 1,
                    line_end INTEGER NOT NULL DEFAULT 1,
                    metadata TEXT,
                    embedding TEXT,
                    FOREIGN KEY (item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS code_symbols (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    file_path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    symbol_type TEXT NOT NULL,
                    signature TEXT,
                    docstring TEXT,
                    line_start INTEGER NOT NULL DEFAULT 1,
                    line_end INTEGER NOT NULL DEFAULT 1,
                    calls TEXT,
                    imports TEXT,
                    parent_symbol TEXT,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS graph_edges (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    weight REAL NOT NULL DEFAULT 1.0,
                    metadata TEXT,
                    PRIMARY KEY (source_id, target_id, relation_type)
                );

                CREATE TABLE IF NOT EXISTS knowledge_conflicts (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    item_a_id TEXT NOT NULL,
                    item_b_id TEXT NOT NULL,
                    statement_a TEXT NOT NULL,
                    statement_b TEXT NOT NULL,
                    source_a TEXT NOT NULL,
                    source_b TEXT NOT NULL,
                    timestamp_a TEXT NOT NULL,
                    timestamp_b TEXT NOT NULL,
                    resolution_status TEXT NOT NULL DEFAULT 'unresolved',
                    resolution_note TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_chunks_item ON knowledge_chunks(item_id);
                CREATE INDEX IF NOT EXISTS idx_items_project ON knowledge_items(project_id);
                CREATE INDEX IF NOT EXISTS idx_items_type ON knowledge_items(type);
                CREATE INDEX IF NOT EXISTS idx_symbols_name ON code_symbols(name);
                CREATE INDEX IF NOT EXISTS idx_symbols_file ON code_symbols(file_path);
                CREATE INDEX IF NOT EXISTS idx_symbols_proj ON code_symbols(project_id);
                CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_id);
                CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_id);
                CREATE INDEX IF NOT EXISTS idx_edges_rel ON graph_edges(relation_type);
                CREATE INDEX IF NOT EXISTS idx_conflicts_topic ON knowledge_conflicts(topic);
                """
            )

    # -------------------------------------------------------------
    # Knowledge Items CRUD
    # -------------------------------------------------------------

    def save_item(self, item: KnowledgeItem) -> KnowledgeItem:
        with self._lock, self._conn:
            item.updated_at = utc_now()
            prov_json = item.provenance.model_dump_json() if item.provenance else None
            meta_json = json.dumps(item.metadata)

            self._conn.execute(
                """
                INSERT INTO knowledge_items (
                    id, type, title, content, summary, source, project_id,
                    created_at, updated_at, permissions_tier, provenance, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type = excluded.type,
                    title = excluded.title,
                    content = excluded.content,
                    summary = excluded.summary,
                    source = excluded.source,
                    project_id = excluded.project_id,
                    updated_at = excluded.updated_at,
                    permissions_tier = excluded.permissions_tier,
                    provenance = excluded.provenance,
                    metadata = excluded.metadata
                """,
                (
                    item.id,
                    item.type.value,
                    item.title,
                    item.content,
                    item.summary,
                    item.source,
                    item.project_id,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                    item.permissions_tier,
                    prov_json,
                    meta_json,
                ),
            )
            # If item has attached chunks, save them too
            if item.chunks:
                for chunk in item.chunks:
                    chunk.item_id = item.id
                self._save_chunks_internal(item.chunks)

        return item

    def get_item(self, item_id: str, include_chunks: bool = True) -> Optional[KnowledgeItem]:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM knowledge_items WHERE id = ?", (item_id,))
            row = cur.fetchone()
            if not row:
                return None
            item = self._row_to_item(row)
            if include_chunks:
                item.chunks = self._get_chunks_for_item_internal(item_id)
            return item

    def delete_item(self, item_id: str) -> bool:
        with self._lock, self._conn:
            # Delete associated chunks
            self._conn.execute("DELETE FROM knowledge_chunks WHERE item_id = ?", (item_id,))
            cur = self._conn.execute("DELETE FROM knowledge_items WHERE id = ?", (item_id,))
            return cur.rowcount > 0

    def list_items(
        self,
        project_id: Optional[str] = None,
        type: Optional[KnowledgeType] = None,
        limit: int = 50,
    ) -> List[KnowledgeItem]:
        query = "SELECT * FROM knowledge_items WHERE 1=1"
        params: List[Any] = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if type:
            query += " AND type = ?"
            params.append(type.value)
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            cur = self._conn.execute(query, tuple(params))
            return [self._row_to_item(r) for r in cur.fetchall()]

    def _row_to_item(self, row: sqlite3.Row) -> KnowledgeItem:
        prov = Provenance.model_validate_json(row["provenance"]) if row["provenance"] else None
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        return KnowledgeItem(
            id=row["id"],
            type=KnowledgeType(row["type"]),
            title=row["title"],
            content=row["content"],
            summary=row["summary"] or "",
            source=row["source"] or "",
            project_id=row["project_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            permissions_tier=row["permissions_tier"],
            provenance=prov,
            metadata=meta,
            chunks=[],
        )

    # -------------------------------------------------------------
    # Chunks Management
    # -------------------------------------------------------------

    def save_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        with self._lock, self._conn:
            self._save_chunks_internal(chunks)

    def _save_chunks_internal(self, chunks: List[KnowledgeChunk]) -> None:
        for c in chunks:
            hierarchy_json = json.dumps(c.heading_hierarchy)
            meta_json = json.dumps(c.metadata)
            emb_json = json.dumps(c.embedding) if c.embedding is not None else None
            self._conn.execute(
                """
                INSERT INTO knowledge_chunks (
                    id, item_id, content, token_count, chunk_index,
                    heading_hierarchy, line_start, line_end, metadata, embedding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    content = excluded.content,
                    token_count = excluded.token_count,
                    chunk_index = excluded.chunk_index,
                    heading_hierarchy = excluded.heading_hierarchy,
                    line_start = excluded.line_start,
                    line_end = excluded.line_end,
                    metadata = excluded.metadata,
                    embedding = excluded.embedding
                """,
                (
                    c.id,
                    c.item_id,
                    c.content,
                    c.token_count,
                    c.chunk_index,
                    hierarchy_json,
                    c.line_start,
                    c.line_end,
                    meta_json,
                    emb_json,
                ),
            )

    def get_chunks_for_item(self, item_id: str) -> List[KnowledgeChunk]:
        with self._lock:
            return self._get_chunks_for_item_internal(item_id)

    def _get_chunks_for_item_internal(self, item_id: str) -> List[KnowledgeChunk]:
        cur = self._conn.execute(
            "SELECT * FROM knowledge_chunks WHERE item_id = ? ORDER BY chunk_index ASC",
            (item_id,),
        )
        return [self._row_to_chunk(r) for r in cur.fetchall()]

    def search_chunks_keyword(
        self,
        query: str,
        project_id: Optional[str] = None,
        types: Optional[List[KnowledgeType]] = None,
        limit: int = 20,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Fast tokenized BM25-like keyword search across chunks and parent item titles.
        Returns list of (KnowledgeChunk, score).
        """
        tokens = [t.lower() for t in query.split() if len(t) > 1]
        if not tokens:
            return []

        conditions = ["1=1"]
        params: List[Any] = []
        if project_id:
            conditions.append("i.project_id = ?")
            params.append(project_id)
        if types:
            placeholders = ",".join("?" for _ in types)
            conditions.append(f"i.type IN ({placeholders})")
            params.extend(t.value for t in types)

        sql = f"""
            SELECT c.*, i.title as item_title, i.project_id as item_proj
            FROM knowledge_chunks c
            JOIN knowledge_items i ON c.item_id = i.id
            WHERE {' AND '.join(conditions)}
        """

        scored_results: List[Tuple[KnowledgeChunk, float]] = []
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            for row in cur.fetchall():
                content_lower = row["content"].lower()
                title_lower = (row["item_title"] or "").lower()
                heading_lower = (row["heading_hierarchy"] or "").lower()

                score = 0.0
                matched_all = True
                for t in tokens:
                    count = content_lower.count(t)
                    title_count = title_lower.count(t)
                    heading_count = heading_lower.count(t)
                    if count == 0 and title_count == 0 and heading_count == 0:
                        matched_all = False
                    # Title & heading matches carry heavier weight
                    score += (count * 1.0) + (title_count * 3.0) + (heading_count * 2.0)

                if score > 0.0:
                    if matched_all:
                        score *= 1.5  # Bonus for containing all search terms
                    chunk = self._row_to_chunk(row)
                    scored_results.append((chunk, score))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:limit]

    def search_chunks_vector(
        self,
        query_vector: List[float],
        project_id: Optional[str] = None,
        types: Optional[List[KnowledgeType]] = None,
        limit: int = 20,
        min_similarity: float = 0.0,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """Dense vector search using cosine similarity across chunk embeddings."""
        if not query_vector:
            return []

        conditions = ["c.embedding IS NOT NULL"]
        params: List[Any] = []
        if project_id:
            conditions.append("i.project_id = ?")
            params.append(project_id)
        if types:
            placeholders = ",".join("?" for _ in types)
            conditions.append(f"i.type IN ({placeholders})")
            params.extend(t.value for t in types)

        sql = f"""
            SELECT c.*, i.project_id as item_proj
            FROM knowledge_chunks c
            JOIN knowledge_items i ON c.item_id = i.id
            WHERE {' AND '.join(conditions)}
        """

        results: List[Tuple[KnowledgeChunk, float]] = []
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            for row in cur.fetchall():
                emb_str = row["embedding"]
                if not emb_str:
                    continue
                emb = json.loads(emb_str)
                sim = cosine_similarity(query_vector, emb)
                if sim >= min_similarity:
                    chunk = self._row_to_chunk(row)
                    results.append((chunk, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _row_to_chunk(self, row: sqlite3.Row) -> KnowledgeChunk:
        hierarchy = json.loads(row["heading_hierarchy"]) if row["heading_hierarchy"] else []
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        emb = json.loads(row["embedding"]) if row["embedding"] else None
        return KnowledgeChunk(
            id=row["id"],
            item_id=row["item_id"],
            content=row["content"],
            token_count=row["token_count"],
            chunk_index=row["chunk_index"],
            heading_hierarchy=hierarchy,
            line_start=row["line_start"],
            line_end=row["line_end"],
            metadata=meta,
            embedding=emb,
        )

    # -------------------------------------------------------------
    # Code Symbols
    # -------------------------------------------------------------

    def save_symbols(self, symbols: List[CodeSymbol]) -> None:
        with self._lock, self._conn:
            for s in symbols:
                self._conn.execute(
                    """
                    INSERT INTO code_symbols (
                        id, project_id, file_path, name, symbol_type,
                        signature, docstring, line_start, line_end,
                        calls, imports, parent_symbol, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        project_id = excluded.project_id,
                        file_path = excluded.file_path,
                        name = excluded.name,
                        symbol_type = excluded.symbol_type,
                        signature = excluded.signature,
                        docstring = excluded.docstring,
                        line_start = excluded.line_start,
                        line_end = excluded.line_end,
                        calls = excluded.calls,
                        imports = excluded.imports,
                        parent_symbol = excluded.parent_symbol,
                        metadata = excluded.metadata
                    """,
                    (
                        s.id,
                        s.project_id,
                        s.file_path,
                        s.name,
                        s.symbol_type.value,
                        s.signature,
                        s.docstring,
                        s.line_start,
                        s.line_end,
                        json.dumps(s.calls),
                        json.dumps(s.imports),
                        s.parent_symbol,
                        json.dumps(s.metadata),
                    ),
                )

    def get_symbols(
        self,
        project_id: Optional[str] = None,
        file_path: Optional[str] = None,
        name: Optional[str] = None,
        symbol_type: Optional[CodeSymbolType] = None,
        limit: int = 100,
    ) -> List[CodeSymbol]:
        conditions = ["1=1"]
        params: List[Any] = []
        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if file_path:
            conditions.append("file_path = ?")
            params.append(file_path)
        if name:
            conditions.append("name LIKE ?")
            params.append(f"%{name}%")
        if symbol_type:
            conditions.append("symbol_type = ?")
            params.append(symbol_type.value)

        sql = f"SELECT * FROM code_symbols WHERE {' AND '.join(conditions)} LIMIT ?"
        params.append(limit)

        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            return [self._row_to_symbol(r) for r in cur.fetchall()]

    def _row_to_symbol(self, row: sqlite3.Row) -> CodeSymbol:
        return CodeSymbol(
            id=row["id"],
            project_id=row["project_id"],
            file_path=row["file_path"],
            name=row["name"],
            symbol_type=CodeSymbolType(row["symbol_type"]),
            signature=row["signature"] or "",
            docstring=row["docstring"] or "",
            line_start=row["line_start"],
            line_end=row["line_end"],
            calls=json.loads(row["calls"]) if row["calls"] else [],
            imports=json.loads(row["imports"]) if row["imports"] else [],
            parent_symbol=row["parent_symbol"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    # -------------------------------------------------------------
    # Graph Edges
    # -------------------------------------------------------------

    def save_edges(self, edges: List[GraphEdge]) -> None:
        with self._lock, self._conn:
            for e in edges:
                self._conn.execute(
                    """
                    INSERT INTO graph_edges (source_id, target_id, relation_type, weight, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(source_id, target_id, relation_type) DO UPDATE SET
                        weight = excluded.weight,
                        metadata = excluded.metadata
                    """,
                    (
                        e.source_id,
                        e.target_id,
                        e.relation_type.value,
                        e.weight,
                        json.dumps(e.metadata),
                    ),
                )

    def get_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
    ) -> List[GraphEdge]:
        conditions = ["1=1"]
        params: List[Any] = []
        if source_id:
            conditions.append("source_id = ?")
            params.append(source_id)
        if target_id:
            conditions.append("target_id = ?")
            params.append(target_id)
        if relation_type:
            conditions.append("relation_type = ?")
            params.append(relation_type.value)

        sql = f"SELECT * FROM graph_edges WHERE {' AND '.join(conditions)}"
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            return [
                GraphEdge(
                    source_id=r["source_id"],
                    target_id=r["target_id"],
                    relation_type=RelationType(r["relation_type"]),
                    weight=float(r["weight"]),
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                )
                for r in cur.fetchall()
            ]

    # -------------------------------------------------------------
    # Conflicts
    # -------------------------------------------------------------

    def save_conflict(self, conflict: KnowledgeConflict) -> KnowledgeConflict:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO knowledge_conflicts (
                    id, topic, item_a_id, item_b_id, statement_a, statement_b,
                    source_a, source_b, timestamp_a, timestamp_b, resolution_status, resolution_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    topic = excluded.topic,
                    resolution_status = excluded.resolution_status,
                    resolution_note = excluded.resolution_note
                """,
                (
                    conflict.id,
                    conflict.topic,
                    conflict.item_a_id,
                    conflict.item_b_id,
                    conflict.statement_a,
                    conflict.statement_b,
                    conflict.source_a,
                    conflict.source_b,
                    conflict.timestamp_a.isoformat(),
                    conflict.timestamp_b.isoformat(),
                    conflict.resolution_status.value,
                    conflict.resolution_note,
                ),
            )
        return conflict

    def get_conflicts(
        self,
        topic: Optional[str] = None,
        unresolved_only: bool = True,
    ) -> List[KnowledgeConflict]:
        conditions = ["1=1"]
        params: List[Any] = []
        if topic:
            conditions.append("topic LIKE ?")
            params.append(f"%{topic}%")
        if unresolved_only:
            conditions.append("resolution_status = 'unresolved'")

        sql = f"SELECT * FROM knowledge_conflicts WHERE {' AND '.join(conditions)}"
        with self._lock:
            cur = self._conn.execute(sql, tuple(params))
            return [
                KnowledgeConflict(
                    id=r["id"],
                    topic=r["topic"],
                    item_a_id=r["item_a_id"],
                    item_b_id=r["item_b_id"],
                    statement_a=r["statement_a"],
                    statement_b=r["statement_b"],
                    source_a=r["source_a"],
                    source_b=r["source_b"],
                    timestamp_a=datetime.fromisoformat(r["timestamp_a"]),
                    timestamp_b=datetime.fromisoformat(r["timestamp_b"]),
                    resolution_status=ConflictResolution(r["resolution_status"]),
                    resolution_note=r["resolution_note"],
                )
                for r in cur.fetchall()
            ]

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: ConflictResolution,
        note: Optional[str] = None,
    ) -> bool:
        with self._lock, self._conn:
            cur = self._conn.execute(
                """
                UPDATE knowledge_conflicts
                SET resolution_status = ?, resolution_note = ?
                WHERE id = ?
                """,
                (resolution.value, note, conflict_id),
            )
            return cur.rowcount > 0

    def close(self) -> None:
        with self._lock:
            self._conn.close()
