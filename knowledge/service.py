"""
SHIVANI Knowledge OS Unified Service Facade
Central orchestration point for workspace indexing, hybrid RAG retrieval,
code intelligence, graph relationships, citations, and conflict detection.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from knowledge.citations.provenance import ProvenanceEngine
from knowledge.code.code_parser import CodeParser
from knowledge.code.symbol_indexer import SymbolIndexer
from knowledge.conflicts.detector import ConflictDetector
from knowledge.embeddings.provider import EmbeddingProvider, get_embedding_provider
from knowledge.graph.graph import KnowledgeGraph
from knowledge.graph.queries import GraphQueries
from knowledge.graph.traversal import GraphTraversal
from knowledge.ingestion.chunker import StructureAwareChunker
from knowledge.ingestion.document_parser import DocumentParser
from knowledge.models import (
    Citation,
    ConflictResolution,
    KnowledgeChunk,
    KnowledgeConflict,
    KnowledgeItem,
    KnowledgeType,
    ProjectProfile,
    Provenance,
    RelationType,
)
from knowledge.projects.project_context import ProjectContext
from knowledge.projects.project_indexer import ProjectIndexer
from knowledge.retrieval.context_assembler import ContextAssembler
from knowledge.retrieval.hybrid_search import HybridSearchEngine
from knowledge.retrieval.reranker import KnowledgeReranker
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


class KnowledgeOS:
    """Unified personal knowledge operating system for SHIVANI."""

    SUPPORTED_EXTENSIONS = {
        ".md", ".markdown", ".txt", ".rst",
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt",
        ".json", ".yaml", ".yml", ".toml", ".csv", ".tsv",
        ".pptx",
    }

    def __init__(
        self,
        db_path: str = "data/knowledge.db",
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.store = SQLiteKnowledgeStore(db_path=db_path)
        self.embeddings = embedding_provider or get_embedding_provider()
        self.doc_parser = DocumentParser(redact_secrets=True)
        self.chunker = StructureAwareChunker()
        self.code_parser = CodeParser()
        self.symbol_indexer = SymbolIndexer(store=self.store, parser=self.code_parser)
        self.project_indexer = ProjectIndexer(store=self.store)
        self.graph = KnowledgeGraph(store=self.store)
        self.search_engine = HybridSearchEngine(
            store=self.store,
            embedding_provider=self.embeddings,
            graph=self.graph,
        )
        self.reranker = KnowledgeReranker()
        self.conflict_detector = ConflictDetector(store=self.store)

    # -------------------------------------------------------------
    # Document & Workspace Indexing
    # -------------------------------------------------------------

    def index_file(
        self,
        file_path: str,
        project_id: Optional[str] = None,
        item_type: Optional[KnowledgeType] = None,
    ) -> Optional[KnowledgeItem]:
        """Parses, sanitizes, chunks, embeds, and indexes a single file."""
        p = Path(file_path).resolve()
        if not p.is_file():
            return None

        ext = p.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return None

        # Determine item type
        if item_type is None:
            if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt"):
                inferred_type = KnowledgeType.CODE_FILE
            else:
                inferred_type = KnowledgeType.DOCUMENT
        else:
            inferred_type = item_type

        # Parse document with secret redaction
        parsed = self.doc_parser.parse_file(str(p))

        # Create knowledge item
        prov = Provenance(
            source_file=str(p),
            line_start=1,
            line_end=parsed.line_count,
        )
        item = KnowledgeItem(
            type=inferred_type,
            title=parsed.title,
            content=parsed.content,
            summary=parsed.content[:200].replace("\n", " ").strip(),
            source=str(p),
            project_id=project_id,
            provenance=prov,
            metadata={
                "file_name": parsed.file_name,
                "extension": parsed.extension,
                "line_count": parsed.line_count,
                "tables_count": len(parsed.tables),
            },
        )

        # Generate structured chunks
        chunks = self.chunker.chunk_document(parsed, item_id=item.id)

        # Generate embeddings for chunks
        chunk_texts = [c.content for c in chunks]
        if chunk_texts:
            embeddings_list = self.embeddings.embed_batch(chunk_texts)
            for c, emb in zip(chunks, embeddings_list):
                c.embedding = emb

        item.chunks = chunks

        # Persist item and chunks
        self.store.save_item(item)

        # If code file, index symbols
        if inferred_type == KnowledgeType.CODE_FILE:
            self.symbol_indexer.index_file(str(p), project_id=project_id)

        return item

    def index_directory(
        self,
        dir_path: str,
        project_id: Optional[str] = None,
        max_files: int = 300,
    ) -> Dict[str, Any]:
        """Indexes an entire directory or workspace project recursively."""
        root = Path(dir_path).resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"Directory not found: {dir_path}")

        # Check and index project profile
        project_profile = None
        try:
            project_profile = self.project_indexer.discover_project(str(root))
            if not project_id:
                project_id = project_profile.id
        except Exception:
            pass

        files_indexed = 0
        chunks_created = 0

        for cur_root, dirs, files in os.walk(root):
            # Exclude vendor and cache dirs
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".")
                and d not in ("node_modules", "__pycache__", "venv", ".venv", "dist", "build", "target")
            ]

            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    fpath = os.path.join(cur_root, fname)
                    item = self.index_file(fpath, project_id=project_id)
                    if item:
                        files_indexed += 1
                        chunks_created += len(item.chunks)
                        if files_indexed >= max_files:
                            break
            if files_indexed >= max_files:
                break

        # Check for conflicts across indexed files
        detected_conflicts = self.conflict_detector.scan_all_conflicts(project_id=project_id)

        return {
            "project_id": project_id,
            "project_name": project_profile.name if project_profile else root.name,
            "files_indexed": files_indexed,
            "chunks_created": chunks_created,
            "conflicts_detected": len(detected_conflicts),
        }

    # -------------------------------------------------------------
    # Search & Retrieval
    # -------------------------------------------------------------

    def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
        rerank: bool = True,
        max_characters: int = 4000,
    ) -> Dict[str, Any]:
        """Executes hybrid retrieval, reranking, and context assembly."""
        raw_candidates = self.search_engine.search(
            query=query,
            project_id=project_id,
            types=types,
            limit=limit * 2,
        )

        if rerank:
            final_candidates = self.reranker.rerank(query, raw_candidates, limit=limit)
        else:
            final_candidates = raw_candidates[:limit]

        assembled = ContextAssembler.assemble(
            final_candidates,
            max_characters=max_characters,
            include_citations=True,
        )

        return {
            "query": query,
            "results_count": len(final_candidates),
            "context": assembled["formatted_context"],
            "citations": assembled["citations"],
            "chunks": [c for c, _ in final_candidates],
        }

    # -------------------------------------------------------------
    # Project Context
    # -------------------------------------------------------------

    def get_project_context(self, project_id_or_path: str) -> str:
        """Returns structured Markdown context summary of the requested project."""
        p = Path(project_id_or_path)
        if p.is_dir():
            profile = self.project_indexer.discover_project(str(p.resolve()))
            return ProjectContext.format_for_prompt(profile)

        # Lookup by ID
        item = self.store.get_item(project_id_or_path)
        if item and item.type == KnowledgeType.PROJECT and item.metadata:
            try:
                prof = ProjectProfile.model_validate(item.metadata)
                return ProjectContext.format_for_prompt(prof)
            except Exception:
                return item.content

        # Fallback to search
        return f"Project profile for '{project_id_or_path}' not found."

    # -------------------------------------------------------------
    # Notes & Decisions
    # -------------------------------------------------------------

    def add_note(
        self,
        title: str,
        content: str,
        project_id: Optional[str] = None,
        is_decision: bool = False,
    ) -> KnowledgeItem:
        """Stores and embeds a personal note or architectural decision."""
        ktype = KnowledgeType.DECISION if is_decision else KnowledgeType.PERSONAL_NOTE
        item = KnowledgeItem(
            type=ktype,
            title=title,
            content=content,
            summary=content[:150].replace("\n", " ").strip(),
            project_id=project_id,
        )
        chunk = KnowledgeChunk(
            item_id=item.id,
            content=content,
            token_count=len(content.split()),
            heading_hierarchy=[title],
            line_start=1,
            line_end=len(content.splitlines()) or 1,
            embedding=self.embeddings.embed_text(content),
        )
        item.chunks = [chunk]
        self.store.save_item(item)
        return item

    # -------------------------------------------------------------
    # Graph Queries
    # -------------------------------------------------------------

    def query_graph(
        self,
        start_node: str,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """Queries graph neighborhood and connections."""
        nodes, edges = GraphTraversal.k_hop_subgraph(self.graph, start_node=start_node, k=max_depth)
        return {
            "start_node": start_node,
            "connected_nodes": nodes,
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relation": e.relation_type.value,
                    "weight": e.weight,
                }
                for e in edges
            ],
        }

    # -------------------------------------------------------------
    # Health & Statistics
    # -------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Returns storage metrics and counts."""
        items = self.store.list_items(limit=1000)
        symbols = self.store.get_symbols(limit=1000)
        conflicts = self.store.get_conflicts(unresolved_only=False)
        return {
            "total_items": len(items),
            "total_symbols": len(symbols),
            "graph_nodes": self.graph.node_count,
            "graph_edges": self.graph.edge_count,
            "conflicts_count": len(conflicts),
        }

    def close(self) -> None:
        self.store.close()


# Global Singleton
_global_knowledge_os: Optional[KnowledgeOS] = None


def get_knowledge_os(db_path: str = "data/knowledge.db") -> KnowledgeOS:
    global _global_knowledge_os
    if _global_knowledge_os is None:
        _global_knowledge_os = KnowledgeOS(db_path=db_path)
    return _global_knowledge_os
