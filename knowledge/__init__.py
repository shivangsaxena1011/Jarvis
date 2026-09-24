"""
SHIVANI Knowledge OS Subsystem
Provides connected knowledge management across projects, documentation, code ASTs,
research sources, personal notes, and architectural decisions.
"""

from knowledge.models import (
    Citation,
    CodeSymbol,
    CodeSymbolType,
    ConflictResolution,
    Entity,
    GraphEdge,
    KnowledgeChunk,
    KnowledgeConflict,
    KnowledgeItem,
    KnowledgeType,
    ProjectProfile,
    Provenance,
    RelationType,
)
from knowledge.service import KnowledgeOS, get_knowledge_os

__all__ = [
    "Citation",
    "CodeSymbol",
    "CodeSymbolType",
    "ConflictResolution",
    "Entity",
    "GraphEdge",
    "KnowledgeChunk",
    "KnowledgeConflict",
    "KnowledgeItem",
    "KnowledgeOS",
    "KnowledgeType",
    "ProjectProfile",
    "Provenance",
    "RelationType",
    "get_knowledge_os",
]

