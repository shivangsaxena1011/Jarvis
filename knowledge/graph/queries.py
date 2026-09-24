"""
SHIVANI Knowledge Graph Query Resolver
Executes semantic graph queries against the workspace graph.
"""

from typing import Any, Dict, List, Optional
from knowledge.graph.graph import KnowledgeGraph
from knowledge.models import RelationType


class GraphQueries:
    """High-level semantic query solver over the knowledge graph."""

    @classmethod
    def get_technologies_used(cls, graph: KnowledgeGraph, project_id: str) -> List[str]:
        """Returns list of technologies/libraries associated with project."""
        techs: List[str] = []
        for target, rel, _ in graph.get_neighbors(project_id, direction="out", relation_type=RelationType.USES_TECHNOLOGY):
            # Target is typically "tech_fastapi", extract clean name
            name = target.replace("tech_", "").title()
            techs.append(name)
        return techs

    @classmethod
    def get_callers(cls, graph: KnowledgeGraph, symbol_id: str) -> List[str]:
        """Returns list of symbols that call the given symbol."""
        callers: List[str] = []
        for caller_id, rel, _ in graph.get_neighbors(symbol_id, direction="in", relation_type=RelationType.CALLS):
            callers.append(caller_id)
        return callers

    @classmethod
    def get_callees(cls, graph: KnowledgeGraph, symbol_id: str) -> List[str]:
        """Returns list of symbols called by the given symbol."""
        callees: List[str] = []
        for callee_id, rel, _ in graph.get_neighbors(symbol_id, direction="out", relation_type=RelationType.CALLS):
            callees.append(callee_id)
        return callees

    @classmethod
    def get_documentation_for_item(cls, graph: KnowledgeGraph, item_id: str) -> List[str]:
        """Returns document IDs describing or referencing the item."""
        docs: List[str] = []
        for doc_id, rel, _ in graph.get_neighbors(item_id, direction="both", relation_type=RelationType.DOCUMENTED_BY):
            docs.append(doc_id)
        return docs
