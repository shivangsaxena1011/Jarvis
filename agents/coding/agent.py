"""
SHIVANI Autonomous Coding Agent
Implements the disciplined AI Software Engineer cycle:
UNDERSTAND ──▶ PLAN ──▶ MODIFY ──▶ TEST ──▶ VERIFY ──▶ REPORT
Enforces strict git safety, secret redaction, and human authorization for commits and pushes.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.coding.models import (
    BuildResult,
    ChangePlan,
    CodeContext,
    ErrorDiagnosis,
    GitStatusInfo,
    PatchResult,
    ProjectSpec,
    TestResult,
)
from agents.coding.detector import ProjectDetector
from agents.coding.git_manager import GitManager
from agents.coding.analyzer import CodeAnalyzer, CodeSearch
from agents.coding.patch_manager import PatchManager
from agents.coding.test_runner import BuildRunner, TestRunner
from agents.coding.error_analyzer import ErrorAnalyzer


class CodingAgent:
    """Professional autonomous software engineer agent."""

    def __init__(self, knowledge_os: Optional[Any] = None):
        self.detector = ProjectDetector()
        self.error_analyzer = ErrorAnalyzer()
        self.knowledge_os = knowledge_os

    def query_codebase_knowledge(self, query: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Queries indexed project blueprints, documentation, and AST symbols via Knowledge OS."""
        if self.knowledge_os:
            return self.knowledge_os.search(query=query, project_id=project_id)
        return {"context": "Knowledge OS not configured.", "citations": []}


    def inspect_project(self, project_path: str) -> Dict[str, Any]:
        """Inspects project structure, languages, frameworks, entrypoints, and git safety."""
        p = Path(project_path).resolve()
        spec = self.detector.detect_project(p)

        git_mgr = GitManager(p)
        # Note: synchronous wrapper returns partial git info if not in async loop
        return {
            "name": spec.name,
            "path": spec.path,
            "languages": spec.languages,
            "frameworks": spec.frameworks,
            "package_manager": spec.package_manager,
            "entry_points": spec.entry_points,
            "test_framework": spec.test_framework,
            "database": spec.database,
            "has_git": spec.has_git,
            "safe_run_command": spec.safe_run_command,
            "test_command": spec.test_command,
            "build_command": spec.build_command,
            "env_vars_detected": spec.env_vars_detected
        }

    async def get_git_status(self, project_path: str) -> GitStatusInfo:
        """Inspects working tree cleanliness and current branch."""
        git_mgr = GitManager(Path(project_path))
        return await git_mgr.get_status()

    def search_code(self, project_path: str, query: str, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches project codebase for matching text or tokens."""
        search = CodeSearch(Path(project_path))
        return search.search_text(query, file_pattern=pattern)

    def find_symbol(self, project_path: str, symbol_name: str) -> List[Dict[str, Any]]:
        """Finds functions and classes across the codebase."""
        search = CodeSearch(Path(project_path))
        return search.find_symbol(symbol_name)

    def read_code_file(self, project_path: str, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
        """Reads file with secret redaction and line slicing."""
        search = CodeSearch(Path(project_path))
        success, content = search.read_file(file_path, start_line, end_line)
        return {"success": success, "file_path": file_path, "content": content}

    def assemble_context(self, project_path: str, query: str) -> CodeContext:
        """Assembles focused context without dumping entire repository."""
        analyzer = CodeAnalyzer(Path(project_path))
        return analyzer.assemble_context_for_task(query)

    def plan_change(self, project_path: str, task: str) -> ChangePlan:
        """Synthesizes structured modification plan and identifies impacted files."""
        ctx = self.assemble_context(project_path, task)
        steps = [
            f"Inspect relevant files: {', '.join(ctx.target_files[:3]) or 'entry points'}",
            f"Draft targeted modifications for task: {task}",
            "Validate syntax and run test suite",
            "Verify unified diff and report changes"
        ]
        return ChangePlan(
            task=task,
            rationale=f"Execute requested modification '{task}' with minimum blast radius.",
            affected_files=ctx.target_files,
            steps=steps,
            potential_risks=["Regression in existing test suite", "Syntax errors during modification"],
            requires_approval=len(ctx.target_files) > 3
        )

    def apply_patch(
        self,
        project_path: str,
        rel_file_path: str,
        target_chunk: str,
        replacement_chunk: str
    ) -> PatchResult:
        """Applies targeted replacement with syntax validation."""
        patcher = PatchManager(Path(project_path))
        return patcher.apply_replacement(rel_file_path, target_chunk, replacement_chunk)

    def create_file(self, project_path: str, rel_file_path: str, content: str) -> PatchResult:
        """Safely creates a new file."""
        patcher = PatchManager(Path(project_path))
        return patcher.create_new_file(rel_file_path, content)

    async def run_tests(self, project_path: str, command: Optional[str] = None, test_path: Optional[str] = None) -> TestResult:
        """Executes test suite and captures structured results."""
        runner = TestRunner(Path(project_path))
        spec = self.detector.detect_project(Path(project_path))
        cmd = command or spec.test_command or "pytest"
        return await runner.run_tests(command=cmd, test_path=test_path)

    async def run_build(self, project_path: str, command: Optional[str] = None) -> BuildResult:
        """Executes build or typecheck."""
        runner = BuildRunner(Path(project_path))
        spec = self.detector.detect_project(Path(project_path))
        cmd = command or spec.build_command or "python -m py_compile main.py"
        return await runner.run_build(command=cmd)

    def analyze_error(self, error_log: str, command: str = "") -> ErrorDiagnosis:
        """Categorizes error and suggests remediation."""
        return self.error_analyzer.analyze_error(error_log, command)

    async def get_diff(self, project_path: str) -> Dict[str, Any]:
        """Calculates unified diff of all uncommitted changes."""
        git_mgr = GitManager(Path(project_path))
        return await git_mgr.get_diff()

    async def commit_changes(self, project_path: str, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Commits changes (strictly requires prior human authorization)."""
        git_mgr = GitManager(Path(project_path))
        return await git_mgr.commit_changes(message, files)

    async def push_changes(self, project_path: str, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """Pushes changes to remote (strictly requires prior human authorization)."""
        git_mgr = GitManager(Path(project_path))
        return await git_mgr.push_changes(remote, branch)
