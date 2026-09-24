"""
SHIVANI Coding Agent Package
"""

from agents.coding.agent import CodingAgent
from agents.coding.detector import ProjectDetector
from agents.coding.git_manager import GitManager
from agents.coding.analyzer import CodeSearch, CodeAnalyzer
from agents.coding.patch_manager import PatchManager
from agents.coding.test_runner import TestRunner, BuildRunner
from agents.coding.error_analyzer import ErrorAnalyzer
from agents.coding.models import (
    ProjectSpec,
    GitStatusInfo,
    CodeContext,
    ChangePlan,
    PatchResult,
    TestResult,
    BuildResult,
    ErrorDiagnosis,
    ErrorCategory,
)

__all__ = [
    "CodingAgent",
    "ProjectDetector",
    "GitManager",
    "CodeSearch",
    "CodeAnalyzer",
    "PatchManager",
    "TestRunner",
    "BuildRunner",
    "ErrorAnalyzer",
    "ProjectSpec",
    "GitStatusInfo",
    "CodeContext",
    "ChangePlan",
    "PatchResult",
    "TestResult",
    "BuildResult",
    "ErrorDiagnosis",
    "ErrorCategory",
]
