"""
SHIVANI Knowledge OS Data Models
Defines unified representations for items, chunks, AST code symbols, entities,
directed graph edges, line-accurate provenance, citations, and conflict tracking.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeType(str, Enum):
    DOCUMENT = "document"
    CODE_FILE = "code_file"
    PROJECT = "project"
    RESEARCH_SOURCE = "research_source"
    DECISION = "decision"
    REQUIREMENT = "requirement"
    PERSONAL_NOTE = "personal_note"
    TASK = "task"
    ARTIFACT = "artifact"
    ENTITY = "entity"
    CONCEPT = "concept"
    ERROR = "error"
    SOLUTION = "solution"


class RelationType(str, Enum):
    USES_TECHNOLOGY = "uses_technology"
    IMPLEMENTS = "implements"
    DOCUMENTED_BY = "documented_by"
    DECIDED_BY = "decided_by"
    TESTED_BY = "tested_by"
    CALLS = "calls"
    IMPORTS = "imports"
    DEPENDS_ON = "depends_on"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    PART_OF = "part_of"
    AUTHORED_BY = "authored_by"
    REFERENCES = "references"


class CodeSymbolType(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    INTERFACE = "interface"
    MODULE = "module"


class ConflictResolution(str, Enum):
    UNRESOLVED = "unresolved"
    A_SUPERSEDES_B = "a_supersedes_b"
    B_SUPERSEDES_A = "b_supersedes_a"
    COEXIST = "coexist"
    MANUAL = "manual"


class Provenance(BaseModel):
    source_file: str
    chunk_index: int = 0
    line_start: int = 1
    line_end: int = 1
    author: Optional[str] = None
    commit_hash: Optional[str] = None
    ingested_at: datetime = Field(default_factory=utc_now)


class KnowledgeChunk(BaseModel):
    id: str = Field(default_factory=lambda: f"chk_{uuid.uuid4().hex[:12]}")
    item_id: str
    content: str
    token_count: int = 0
    chunk_index: int = 0
    heading_hierarchy: List[str] = Field(default_factory=list)
    line_start: int = 1
    line_end: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class CodeSymbol(BaseModel):
    id: str = Field(default_factory=lambda: f"sym_{uuid.uuid4().hex[:12]}")
    project_id: Optional[str] = None
    file_path: str
    name: str
    symbol_type: CodeSymbolType
    signature: str = ""
    docstring: str = ""
    line_start: int = 1
    line_end: int = 1
    calls: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    parent_symbol: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Entity(BaseModel):
    id: str = Field(default_factory=lambda: f"ent_{uuid.uuid4().hex[:12]}")
    name: str
    entity_type: str
    description: str = ""
    aliases: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    claim: str
    source_id: str
    source_title: str
    source_uri: str
    snippet: str
    line_start: int
    line_end: int
    confidence: float = 1.0

    def to_footnote(self, index: int) -> str:
        """Formats citation as a clean Markdown footnote link."""
        return f"[^{index}]: [{self.source_title}:{self.line_start}-{self.line_end}]({self.source_uri}#L{self.line_start}-L{self.line_end}) — \"{self.snippet.strip()[:100]}\""


class KnowledgeConflict(BaseModel):
    id: str = Field(default_factory=lambda: f"cnf_{uuid.uuid4().hex[:12]}")
    topic: str
    item_a_id: str
    item_b_id: str
    statement_a: str
    statement_b: str
    source_a: str
    source_b: str
    timestamp_a: datetime = Field(default_factory=utc_now)
    timestamp_b: datetime = Field(default_factory=utc_now)
    resolution_status: ConflictResolution = ConflictResolution.UNRESOLVED
    resolution_note: Optional[str] = None


class KnowledgeItem(BaseModel):
    id: str = Field(default_factory=lambda: f"kno_{uuid.uuid4().hex[:12]}")
    type: KnowledgeType
    title: str
    content: str
    summary: str = ""
    source: str = ""
    project_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    permissions_tier: str = "internal"
    provenance: Optional[Provenance] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunks: List[KnowledgeChunk] = Field(default_factory=list)


class ProjectProfile(BaseModel):
    id: str
    name: str
    root_path: str
    version: Optional[str] = None
    repository_url: Optional[str] = None
    git_branch: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    package_managers: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    test_frameworks: List[str] = Field(default_factory=list)
    architecture_overview: str = ""
    key_documents: List[str] = Field(default_factory=list)
    key_symbols_count: int = 0
    total_files_indexed: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
