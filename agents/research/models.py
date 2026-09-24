"""
SHIVANI Research Agent Data Models
Structured data contracts for source records, source classification,
contradiction records, and synthesized research bundles.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PRIMARY = "primary"        # Academic papers (arXiv), official standards/RFCs, vendor docs
    SECONDARY = "secondary"    # Reputable engineering blogs, tech publications, benchmarks
    COMMUNITY = "community"    # Forum posts, social threads, informal articles


class SourceRecord(BaseModel):
    """Structured bibliographic and provenance record for a research source."""
    id: str
    title: str
    url: str
    publisher: str
    date: str
    source_type: SourceType
    relevance: float = Field(ge=0.0, le=1.0)
    summary: str
    author: Optional[str] = None
    doi_or_id: Optional[str] = None


class ContradictionRecord(BaseModel):
    """Documents conflicting claims or differing benchmarks between sources."""
    topic: str
    perspective_a: str
    source_a_id: str
    perspective_b: str
    source_b_id: str
    analysis: str


class ResearchBundle(BaseModel):
    """Complete synthesized research outcome artifact."""
    query: str
    timestamp: str
    executive_summary: str
    problem: str
    existing_approaches: List[str] = Field(default_factory=list)
    technology_landscape: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    comparison_matrix: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    contradictions: List[ContradictionRecord] = Field(default_factory=list)
    sources: List[SourceRecord] = Field(default_factory=list)
    markdown_report: str = ""
