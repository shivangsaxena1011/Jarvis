"""
Unit Tests for AST Code Parser and Symbol Indexer
"""

from pathlib import Path
import pytest
from knowledge.code.code_parser import CodeParser
from knowledge.code.symbol_indexer import SymbolIndexer
from knowledge.models import CodeSymbolType, RelationType
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


def test_python_ast_parsing(tmp_path):
    code_file = tmp_path / "service.py"
    content = '''"""Service module docstring."""
import os
from pathlib import Path

class UserManager:
    """Manages users."""
    def __init__(self, db_path: str):
        self.db = db_path

    async def get_user(self, user_id: str) -> dict:
        """Fetches user by id."""
        return self._lookup(user_id)

    def _lookup(self, uid: str) -> dict:
        return {"id": uid}

def create_default_manager() -> UserManager:
    return UserManager("data/users.db")
'''
    code_file.write_text(content, encoding="utf-8")

    parser = CodeParser()
    symbols = parser.parse_file(str(code_file))

    # Should have MODULE, CLASS UserManager, METHOD __init__, METHOD get_user, METHOD _lookup, FUNCTION create_default_manager
    names = {s.name for s in symbols}
    assert "UserManager" in names
    assert "UserManager.get_user" in names
    assert "UserManager._lookup" in names
    assert "create_default_manager" in names

    # Check method details
    get_user_sym = next(s for s in symbols if s.name == "UserManager.get_user")
    assert get_user_sym.symbol_type == CodeSymbolType.METHOD
    assert "async def get_user" in get_user_sym.signature
    assert "Fetches user by id" in get_user_sym.docstring
    assert "self._lookup" in get_user_sym.calls


def test_symbol_indexing_and_graph_edges(tmp_path):
    code_file = tmp_path / "app.py"
    code_file.write_text('''
class Controller:
    def handle_request(self):
        self.process()

    def process(self):
        pass
''', encoding="utf-8")

    store = SQLiteKnowledgeStore(db_path=":memory:")
    indexer = SymbolIndexer(store=store)
    symbols = indexer.index_file(str(code_file))

    assert len(symbols) >= 3

    # Check edges in store
    edges = store.get_edges()
    assert len(edges) >= 2  # Part_of edges and call edges
    part_of_edges = [e for e in edges if e.relation_type == RelationType.PART_OF]
    assert len(part_of_edges) >= 2

    store.close()
