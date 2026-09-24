"""
SHIVANI GitHub Registered Tools
Registered tools for repository inspection, file reading, issues, and safe project startup.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from integrations.github.service import GitHubService


class GitHubInspectArgs(BaseModel):
    repo_path_or_name: str = Field(description="Local project path, project name, or GitHub repository URL")


class GitHubInspectRepositoryTool(BaseTool):
    name = "github.inspect_repository"
    description = "Inspect repository README, tech stack, entrypoints, files, and git configuration."
    permission_level = RiskLevel.SAFE
    args_schema = GitHubInspectArgs
    timeout = 20.0

    def __init__(self, github_service: Optional[GitHubService] = None):
        super().__init__()
        self.service = github_service or GitHubService()

    async def run(self, repo_path_or_name: str) -> Dict[str, Any]:
        return await self.service.inspect_repository(repo_path_or_name)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False)}


class GitHubReadFileArgs(BaseModel):
    repo_path: str = Field(description="Repository directory path")
    file_path: str = Field(description="Relative path of file inside repository")


class GitHubReadFileTool(BaseTool):
    name = "github.read_file"
    description = "Read source code or documentation file inside a repository."
    permission_level = RiskLevel.SAFE
    args_schema = GitHubReadFileArgs
    timeout = 15.0

    def __init__(self, github_service: Optional[GitHubService] = None):
        super().__init__()
        self.service = github_service or GitHubService()

    async def run(self, repo_path: str, file_path: str) -> Dict[str, Any]:
        return await self.service.read_file(repo_path, file_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("content"))}


class GitHubListFilesArgs(BaseModel):
    repo_path: str = Field(description="Repository directory path")
    subpath: str = Field(default="", description="Optional subfolder path inside repository")


class GitHubListFilesTool(BaseTool):
    name = "github.list_files"
    description = "List files and directories in a repository."
    permission_level = RiskLevel.SAFE
    args_schema = GitHubListFilesArgs
    timeout = 15.0

    def __init__(self, github_service: Optional[GitHubService] = None):
        super().__init__()
        self.service = github_service or GitHubService()

    async def run(self, repo_path: str, subpath: str = "") -> Dict[str, Any]:
        files = await self.service.list_files(repo_path, subpath)
        return {"count": len(files), "files": files}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "count": result_data.get("count", 0)}


class GitHubReadIssuesArgs(BaseModel):
    repo_path_or_url: str = Field(description="Repository path or URL")


class GitHubReadIssuesTool(BaseTool):
    name = "github.read_issues"
    description = "Read open issues and tracker details for a repository."
    permission_level = RiskLevel.SAFE
    args_schema = GitHubReadIssuesArgs
    timeout = 20.0

    def __init__(self, github_service: Optional[GitHubService] = None):
        super().__init__()
        self.service = github_service or GitHubService()

    async def run(self, repo_path_or_url: str) -> Dict[str, Any]:
        issues = await self.service.read_issues(repo_path_or_url)
        return {"count": len(issues), "issues": issues}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True}


class GitHubCreateIssueArgs(BaseModel):
    repo_path: str = Field(description="Repository path")
    title: str = Field(description="Issue title")
    body: str = Field(description="Issue body description")


class GitHubCreateIssueTool(BaseTool):
    name = "github.create_issue"
    description = "Create a new issue in repository (Requires SENSITIVE confirmation)."
    permission_level = RiskLevel.SENSITIVE
    args_schema = GitHubCreateIssueArgs
    requires_confirmation = True
    timeout = 20.0

    def __init__(self, github_service: Optional[GitHubService] = None):
        super().__init__()
        self.service = github_service or GitHubService()

    async def run(self, repo_path: str, title: str, body: str) -> Dict[str, Any]:
        return await self.service.create_issue(repo_path, title, body)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False)}


class GitHubInspectRunnableArgs(BaseModel):
    repo_path: str = Field(description="Local repository directory path")


class GitHubInspectRunnableTool(BaseTool):
    name = "github.inspect_runnable"
    description = "Inspect repository dependencies and determine safe verified startup command."
    permission_level = RiskLevel.SAFE
    args_schema = GitHubInspectRunnableArgs
    timeout = 15.0

    def __init__(self, github_service: Optional[GitHubService] = None):
        super().__init__()
        self.service = github_service or GitHubService()

    async def run(self, repo_path: str) -> Dict[str, Any]:
        return await self.service.inspect_runnable_service(repo_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("command"))}
