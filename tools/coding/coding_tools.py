"""
SHIVANI Coding Registered Tools
Registered tools for project inspection, code search, symbol discovery, syntax-validated patching,
testing, error analysis, and git operations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from agents.coding.agent import CodingAgent


class CodingInspectProjectArgs(BaseModel):
    project_path: str = Field(description="Local path to software project directory")


class CodingInspectProjectTool(BaseTool):
    name = "coding.inspect_project"
    description = "Inspect project directory and detect languages, frameworks, package manager, and entry points."
    permission_level = RiskLevel.SAFE
    args_schema = CodingInspectProjectArgs
    timeout = 20.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str) -> Dict[str, Any]:
        return self.agent.inspect_project(project_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("name")) and bool(result_data.get("languages"))}


class CodingSearchCodeArgs(BaseModel):
    project_path: str = Field(description="Project root path")
    query: str = Field(description="Keyword, token, or pattern to search for")
    pattern: Optional[str] = Field(default=None, description="Glob pattern e.g. '*.py' or '*.ts'")


class CodingSearchCodeTool(BaseTool):
    name = "coding.search_code"
    description = "Search project codebase for matching text or tokens."
    permission_level = RiskLevel.SAFE
    args_schema = CodingSearchCodeArgs
    timeout = 20.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str, query: str, pattern: Optional[str] = None) -> Dict[str, Any]:
        results = self.agent.search_code(project_path, query, pattern)
        return {"count": len(results), "matches": results}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "count": result_data.get("count", 0)}


class CodingFindSymbolArgs(BaseModel):
    project_path: str = Field(description="Project root path")
    symbol_name: str = Field(description="Function or class name to search for")


class CodingFindSymbolTool(BaseTool):
    name = "coding.find_symbol"
    description = "Locate class and function definitions across codebase using AST analysis."
    permission_level = RiskLevel.SAFE
    args_schema = CodingFindSymbolArgs
    timeout = 20.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str, symbol_name: str) -> Dict[str, Any]:
        symbols = self.agent.find_symbol(project_path, symbol_name)
        return {"count": len(symbols), "symbols": symbols}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "count": result_data.get("count", 0)}


class CodingReadCodeFileArgs(BaseModel):
    project_path: str = Field(description="Project root path")
    file_path: str = Field(description="Relative file path within project")
    start_line: Optional[int] = Field(default=None, description="Starting line number (1-indexed)")
    end_line: Optional[int] = Field(default=None, description="Ending line number (1-indexed)")


class CodingReadCodeFileTool(BaseTool):
    name = "coding.read_code_file"
    description = "Read file content with secret redaction and line range slicing."
    permission_level = RiskLevel.SAFE
    args_schema = CodingReadCodeFileArgs
    timeout = 15.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Dict[str, Any]:
        return self.agent.read_code_file(project_path, file_path, start_line, end_line)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class CodingApplyPatchArgs(BaseModel):
    project_path: str = Field(description="Project root path")
    file_path: str = Field(description="Relative file path to modify")
    target_chunk: str = Field(description="Exact existing lines to replace")
    replacement_chunk: str = Field(description="New replacement lines")


class CodingApplyPatchTool(BaseTool):
    name = "coding.apply_patch"
    description = "Apply targeted code modification with syntax validation and unified diff tracking."
    permission_level = RiskLevel.SENSITIVE
    requires_confirmation = True
    args_schema = CodingApplyPatchArgs
    timeout = 25.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str, file_path: str, target_chunk: str, replacement_chunk: str) -> Dict[str, Any]:
        res = self.agent.apply_patch(project_path, file_path, target_chunk, replacement_chunk)
        return res.model_dump()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class CodingCreateFileArgs(BaseModel):
    project_path: str = Field(description="Project root path")
    file_path: str = Field(description="Relative file path to create")
    content: str = Field(description="File content")


class CodingCreateFileTool(BaseTool):
    name = "coding.create_file"
    description = "Safely create a new file in the repository with syntax validation."
    permission_level = RiskLevel.SENSITIVE
    requires_confirmation = True
    args_schema = CodingCreateFileArgs
    timeout = 20.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str, file_path: str, content: str) -> Dict[str, Any]:
        res = self.agent.create_file(project_path, file_path, content)
        return res.model_dump()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class CodingRunTestsArgs(BaseModel):
    project_path: str = Field(description="Project root path")
    command: Optional[str] = Field(default=None, description="Test command override")
    test_path: Optional[str] = Field(default=None, description="Specific test file or directory")


class CodingRunTestsTool(BaseTool):
    name = "coding.run_tests"
    description = "Run automated project test suite (pytest, npm test, etc.) and capture results."
    permission_level = RiskLevel.SAFE
    args_schema = CodingRunTestsArgs
    timeout = 90.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str, command: Optional[str] = None, test_path: Optional[str] = None) -> Dict[str, Any]:
        res = await self.agent.run_tests(project_path, command, test_path)
        return res.model_dump()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("exit_code") is not None}


class CodingRunBuildArgs(BaseModel):
    project_path: str = Field(description="Project root path")
    command: Optional[str] = Field(default=None, description="Build command override")


class CodingRunBuildTool(BaseTool):
    name = "coding.run_build"
    description = "Execute project build or typecheck pipeline."
    permission_level = RiskLevel.SAFE
    args_schema = CodingRunBuildArgs
    timeout = 90.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str, command: Optional[str] = None) -> Dict[str, Any]:
        res = await self.agent.run_build(project_path, command)
        return res.model_dump()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("exit_code") is not None}


class CodingAnalyzeErrorArgs(BaseModel):
    error_log: str = Field(description="Raw stderr or stack trace from failed command")
    command: str = Field(default="", description="Command that failed")


class CodingAnalyzeErrorTool(BaseTool):
    name = "coding.analyze_error"
    description = "Diagnose root cause and prescribe fixes for build, test, or runtime error."
    permission_level = RiskLevel.SAFE
    args_schema = CodingAnalyzeErrorArgs
    timeout = 15.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, error_log: str, command: str = "") -> Dict[str, Any]:
        diag = self.agent.analyze_error(error_log, command)
        return diag.model_dump()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("category")) and bool(result_data.get("suggested_action"))}


class CodingGitStatusArgs(BaseModel):
    project_path: str = Field(description="Project root path")


class CodingGitStatusTool(BaseTool):
    name = "coding.git_status"
    description = "Check git status, current branch, and clean/dirty working tree state."
    permission_level = RiskLevel.SAFE
    args_schema = CodingGitStatusArgs
    timeout = 15.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str) -> Dict[str, Any]:
        st = await self.agent.get_git_status(project_path)
        return st.model_dump()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "is_git": result_data.get("is_git", False)}


class CodingGitDiffArgs(BaseModel):
    project_path: str = Field(description="Project root path")


class CodingGitDiffTool(BaseTool):
    name = "coding.git_diff"
    description = "Calculate unified diff and line change counts for all uncommitted modifications."
    permission_level = RiskLevel.SAFE
    args_schema = CodingGitDiffArgs
    timeout = 15.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str) -> Dict[str, Any]:
        return await self.agent.get_diff(project_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": "files_changed" in result_data}


class CodingGitCommitArgs(BaseModel):
    project_path: str = Field(description="Project root path")
    message: str = Field(description="Commit message")
    files: Optional[List[str]] = Field(default=None, description="Optional specific files to stage")


class CodingGitCommitTool(BaseTool):
    name = "coding.git_commit"
    description = "Create a git commit (Strictly requires explicit human approval)."
    permission_level = RiskLevel.SENSITIVE
    requires_confirmation = True
    args_schema = CodingGitCommitArgs
    timeout = 20.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        return await self.agent.commit_changes(project_path, message, files)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class CodingGitPushArgs(BaseModel):
    project_path: str = Field(description="Project root path")
    remote: str = Field(default="origin", description="Remote name")
    branch: Optional[str] = Field(default=None, description="Branch to push")


class CodingGitPushTool(BaseTool):
    name = "coding.git_push"
    description = "Push commits to remote repository (Strictly requires explicit human approval)."
    permission_level = RiskLevel.CRITICAL
    requires_confirmation = True
    args_schema = CodingGitPushArgs
    timeout = 30.0

    def __init__(self, coding_agent: Optional[CodingAgent] = None):
        super().__init__()
        self.agent = coding_agent or CodingAgent()

    async def run(self, project_path: str, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        return await self.agent.push_changes(project_path, remote, branch)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}
