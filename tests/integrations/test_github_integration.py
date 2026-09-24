"""
Unit & Integration Tests for SHIVANI GitHub Integration & Tools.
"""

import pytest
from pathlib import Path
from integrations.github.service import GitHubService
from tools.integrations.github_tools import (
    GitHubInspectRepositoryTool,
    GitHubReadFileTool,
    GitHubListFilesTool,
    GitHubReadIssuesTool,
    GitHubCreateIssueTool,
    GitHubInspectRunnableTool,
)


@pytest.fixture
def temp_repo(tmp_path):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    readme = repo_dir / "README.md"
    readme.write_text("# Sample Project\nA Python FastAPI application for data analysis.", encoding="utf-8")
    
    app_py = repo_dir / "app.py"
    app_py.write_text("print('Running application')", encoding="utf-8")
    
    reqs = repo_dir / "requirements.txt"
    reqs.write_text("fastapi\nuvicorn\n", encoding="utf-8")
    
    return str(repo_dir)


@pytest.mark.asyncio
async def test_github_inspect_and_runnable(temp_repo):
    """Verify GitHubService inspects repository files and determines safe startup command."""
    service = GitHubService()
    
    # 1. Inspect repository
    info = await service.inspect_repository(temp_repo)
    assert info["status"] == "success"
    assert info["has_readme"] is True
    assert "Python" in info["languages"]
    assert "FastAPI" in info["frameworks"]
    
    # 2. Inspect runnable service
    runnable = await service.inspect_runnable_service(temp_repo)
    assert runnable["status"] == "analyzed"
    assert runnable["is_runnable"] is True
    assert "python" in runnable["command"].lower() or "uvicorn" in runnable["command"].lower()


@pytest.mark.asyncio
async def test_github_file_operations(temp_repo):
    """Verify reading repository files and listing repository contents."""
    service = GitHubService()
    
    # List files
    files = await service.list_files(temp_repo)
    assert "README.md" in files
    assert "app.py" in files
    
    # Read file
    content_res = await service.read_file(temp_repo, "README.md")
    assert content_res["status"] == "success"
    assert "Sample Project" in content_res["content"]


@pytest.mark.asyncio
async def test_github_registered_tools(temp_repo):
    """Verify all registered GitHub tools execute and verify cleanly."""
    service = GitHubService()
    
    inspect_tool = GitHubInspectRepositoryTool(github_service=service)
    read_tool = GitHubReadFileTool(github_service=service)
    list_tool = GitHubListFilesTool(github_service=service)
    runnable_tool = GitHubInspectRunnableTool(github_service=service)
    issues_tool = GitHubReadIssuesTool(github_service=service)
    create_issue_tool = GitHubCreateIssueTool(github_service=service)
    
    # 1. Inspect
    i_res = await inspect_tool.run(repo_path_or_name=temp_repo)
    assert (await inspect_tool.verify(i_res))["verified"] is True
    
    # 2. List
    l_res = await list_tool.run(repo_path=temp_repo)
    assert (await list_tool.verify(l_res))["verified"] is True
    
    # 3. Read
    r_res = await read_tool.run(repo_path=temp_repo, file_path="README.md")
    assert (await read_tool.verify(r_res))["verified"] is True
    
    # 4. Runnable
    rn_res = await runnable_tool.run(repo_path=temp_repo)
    assert (await runnable_tool.verify(rn_res))["verified"] is True
    
    # 5. Read issues
    iss_res = await issues_tool.run(repo_path_or_url=temp_repo)
    assert (await issues_tool.verify(iss_res))["verified"] is True
    
    # 6. Create issue
    ci_res = await create_issue_tool.run(repo_path=temp_repo, title="Bug in parser", body="Details here")
    assert (await create_issue_tool.verify(ci_res))["verified"] is True
