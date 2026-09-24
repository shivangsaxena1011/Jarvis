"""
SHIVANI Symbol Indexer
Indexes AST code symbols into the SQLite knowledge store and generates
directed call graphs and dependency edges.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from knowledge.code.code_parser import CodeParser
from knowledge.models import CodeSymbol, CodeSymbolType, GraphEdge, RelationType
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


class SymbolIndexer:
    """Extracts and indexes code symbols, resolving call and import relations."""

    CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt", ".go", ".rs"}

    def __init__(self, store: SQLiteKnowledgeStore, parser: Optional[CodeParser] = None):
        self.store = store
        self.parser = parser or CodeParser()

    def index_file(self, file_path: str, project_id: Optional[str] = None) -> List[CodeSymbol]:
        """Parses and stores symbols from a single code file, generating graph edges."""
        symbols = self.parser.parse_file(file_path, project_id=project_id)
        if not symbols:
            return []

        # Save symbols
        self.store.save_symbols(symbols)

        # Build graph edges
        edges: List[GraphEdge] = []
        module_sym = next((s for s in symbols if s.symbol_type == CodeSymbolType.MODULE), None)
        class_syms = {s.name: s for s in symbols if s.symbol_type == CodeSymbolType.CLASS}

        for s in symbols:
            # Method part of class
            if s.parent_symbol and s.parent_symbol in class_syms:
                edges.append(
                    GraphEdge(
                        source_id=s.id,
                        target_id=class_syms[s.parent_symbol].id,
                        relation_type=RelationType.PART_OF,
                        weight=1.0,
                    )
                )
            # Symbol part of file/module
            elif module_sym and s.id != module_sym.id:
                edges.append(
                    GraphEdge(
                        source_id=s.id,
                        target_id=module_sym.id,
                        relation_type=RelationType.PART_OF,
                        weight=1.0,
                    )
                )

            # Internal calls to other symbols in the same file
            for call_name in s.calls:
                # Direct function name or method name
                target = next((cand for cand in symbols if cand.name.endswith(call_name)), None)
                if target and target.id != s.id:
                    edges.append(
                        GraphEdge(
                            source_id=s.id,
                            target_id=target.id,
                            relation_type=RelationType.CALLS,
                            weight=1.0,
                        )
                    )

            # Module imports
            if s.symbol_type == CodeSymbolType.MODULE:
                for imp in s.imports:
                    edges.append(
                        GraphEdge(
                            source_id=s.id,
                            target_id=f"mod_{imp}",
                            relation_type=RelationType.IMPORTS,
                            weight=1.0,
                            metadata={"module": imp},
                        )
                    )

        if edges:
            self.store.save_edges(edges)

        return symbols

    def index_directory(
        self,
        dir_path: str,
        project_id: Optional[str] = None,
        max_files: int = 500,
    ) -> int:
        """Indexes all code files in directory recursively."""
        root = Path(dir_path).resolve()
        if not root.is_dir():
            return 0

        total_symbols = 0
        file_count = 0

        for cur_root, dirs, files in os.walk(root):
            # Skip hidden and dependency directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d not in ("node_modules", "__pycache__", "venv", ".venv", "dist", "build")
            ]

            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext in self.CODE_EXTENSIONS:
                    fpath = os.path.join(cur_root, fname)
                    syms = self.index_file(fpath, project_id=project_id)
                    total_symbols += len(syms)
                    file_count += 1
                    if file_count >= max_files:
                        return total_symbols

        return total_symbols
