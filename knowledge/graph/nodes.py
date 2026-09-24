"""
SHIVANI Knowledge Graph Nodes
Defines graph node abstractions representing documents, code symbols, entities, and projects.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Represents a discrete entity or item in the knowledge graph."""
    id: str
    name: str
    node_type: str = "item"
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
