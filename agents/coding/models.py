"""
SHIVANI Coding Agent Data Models
Structured data contracts for project detection, code search, patching, testing, and error diagnosis.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    SYNTAX = "syntax"
    DEPENDENCY = "dependency"
    TYPE_ERROR = "type"
    RUNTIME = "runtime"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    DATABASE = "database"
    ENVIRONMENT = "environment"
    UNKNOWN = "unknown"


class ProjectSpec(BaseModel):
    """Detailed structural specification of a detected software project."""
    name: str
    path: str
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    package_manager: Optional[str] = None
    entry_points: List[str] = Field(default_factory=list)
    build_system: Optional[str] = None
    test_framework: Optional[str] = None
    database: Optional[str] = None
    has_git: bool = False
    is_git_dirty: bool = False
    git_branch: Optional[str] = None
    safe_run_command: Optional[str] = None
    test_command: Optional[str] = None
    build_command: Optional[str] = None
    env_vars_detected: List[str] = Field(default_factory=list)


class GitStatusInfo(BaseModel):
    """Encapsulates Git repository status and safety indicators."""
    is_git: bool
    branch: str = "main"
    is_clean: bool = True
    modified_files: List[str] = Field(default_factory=list)
    untracked_files: List[str] = Field(default_factory=list)
    staged_files: List[str] = Field(default_factory=list)
    remote_url: Optional[str] = None
    checkpoint_branch: Optional[str] = None


class CodeContext(BaseModel):
    """Focused repository subset context for LLM reasoning."""
    target_files: List[str] = Field(default_factory=list)
    file_contents: Dict[str, str] = Field(default_factory=dict)
    relevant_symbols: List[str] = Field(default_factory=list)
    architecture_summary: str = ""


class ChangePlan(BaseModel):
    """Structured plan for code modification."""
    task: str
    rationale: str
    affected_files: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    potential_risks: List[str] = Field(default_factory=list)
    requires_approval: bool = False


class PatchResult(BaseModel):
    """Result of a code patching operation."""
    file_path: str
    success: bool
    unified_diff: str = ""
    lines_added: int = 0
    lines_removed: int = 0
    error: Optional[str] = None


class TestResult(BaseModel):
    """Structured result of executing a project test suite."""
    command: str
    success: bool
    exit_code: int
    passed_count: int = 0
    failed_count: int = 0
    stdout: str = ""
    stderr: str = ""
    failed_tests: List[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0


class BuildResult(BaseModel):
    """Structured result of executing a project build or typecheck."""
    command: str
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0


class ErrorDiagnosis(BaseModel):
    """Diagnostic output from ErrorAnalyzer."""
    category: ErrorCategory
    root_cause: str
    error_summary: str
    suggested_action: str
    missing_packages: List[str] = Field(default_factory=list)
    requires_confirmation: bool = False
