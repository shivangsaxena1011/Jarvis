"""
Unit & Integration Tests for SHIVANI Coding Agent & Tools.
Tests project detection, git safety, code search, secret redaction,
syntax-validated patching, test execution, error diagnosis, and registered tools.
"""

import pytest
from pathlib import Path
from agents.coding.agent import CodingAgent
from agents.coding.detector import ProjectDetector
from agents.coding.error_analyzer import ErrorAnalyzer
from agents.coding.models import ErrorCategory
from tools.coding import (
    CodingInspectProjectTool,
    CodingSearchCodeTool,
    CodingFindSymbolTool,
    CodingReadCodeFileTool,
    CodingApplyPatchTool,
    CodingCreateFileTool,
    CodingRunTestsTool,
    CodingAnalyzeErrorTool,
    CodingGitStatusTool,
    CodingGitDiffTool,
)


@pytest.fixture
def sample_python_project(tmp_path):
    proj_dir = tmp_path / "sample_service"
    proj_dir.mkdir()

    # README
    (proj_dir / "README.md").write_text("# Sample Service\nFastAPI backend application.", encoding="utf-8")

    # pyproject.toml
    (proj_dir / "pyproject.toml").write_text(
        '[project]\nname = "sample-service"\nversion = "0.1.0"\ndependencies = ["fastapi", "uvicorn", "pytest"]\n',
        encoding="utf-8"
    )

    # .env with secrets
    (proj_dir / ".env").write_text(
        'DATABASE_URL=sqlite:///./app.db\nAPI_KEY="sk-secret-key-123456789"\nJWT_SECRET=super_secret_token_abc\n',
        encoding="utf-8"
    )

    # main.py
    main_code = (
        'from fastapi import FastAPI\n\n'
        'app = FastAPI(title="Sample Service")\n\n'
        '@app.get("/health")\n'
        'def health_check():\n'
        '    """Returns service health status."""\n'
        '    return {"status": "healthy", "service": "sample"}\n'
    )
    (proj_dir / "main.py").write_text(main_code, encoding="utf-8")

    # tests directory
    tests_dir = proj_dir / "tests"
    tests_dir.mkdir()
    test_code = (
        'def test_dummy():\n'
        '    assert 1 + 1 == 2\n'
    )
    (tests_dir / "test_sample.py").write_text(test_code, encoding="utf-8")

    return proj_dir


def test_project_detector_python_fastapi(sample_python_project):
    """Verify detector correctly identifies language, framework, entrypoints, and env variables."""
    detector = ProjectDetector()
    spec = detector.detect_project(sample_python_project)

    assert "Python" in spec.languages
    assert "FastAPI" in spec.frameworks
    assert "main.py" in spec.entry_points
    assert spec.test_framework == "pytest"
    assert "API_KEY" in spec.env_vars_detected
    assert "DATABASE_URL" in spec.env_vars_detected
    assert "JWT_SECRET" in spec.env_vars_detected


def test_code_search_and_secret_redaction(sample_python_project):
    """Verify code search retrieves lines and redacts secret values."""
    agent = CodingAgent()
    proj_str = str(sample_python_project)

    # Search text
    matches = agent.search_code(proj_str, "health_check")
    assert len(matches) >= 1
    assert matches[0]["file"] == "main.py"

    # Find symbol
    symbols = agent.find_symbol(proj_str, "health_check")
    assert len(symbols) >= 1
    assert symbols[0]["name"] == "health_check"

    # Read file with secret redaction
    read_res = agent.read_code_file(proj_str, ".env")
    assert read_res["success"] is True
    assert "[REDACTED]" in read_res["content"]
    assert "sk-secret-key" not in read_res["content"]


def test_targeted_patch_and_syntax_validation(sample_python_project):
    """Verify targeted replacement succeeds on valid syntax and blocks on invalid syntax."""
    agent = CodingAgent()
    proj_str = str(sample_python_project)

    # 1. Valid replacement
    patch_res = agent.apply_patch(
        project_path=proj_str,
        rel_file_path="main.py",
        target_chunk='    return {"status": "healthy", "service": "sample"}\n',
        replacement_chunk='    return {"status": "healthy", "service": "sample", "version": "1.0"}\n'
    )
    assert patch_res.success is True
    assert patch_res.lines_added >= 1
    assert "version" in patch_res.unified_diff

    # Verify content modified on disk
    read_back = (sample_python_project / "main.py").read_text(encoding="utf-8")
    assert '"version": "1.0"' in read_back

    # 2. Invalid syntax replacement should be blocked before write
    bad_res = agent.apply_patch(
        project_path=proj_str,
        rel_file_path="main.py",
        target_chunk='def health_check():\n',
        replacement_chunk='def health_check( missing_colon\n'
    )
    assert bad_res.success is False
    assert "Syntax error" in bad_res.error


def test_error_analyzer_classification():
    """Verify error analyzer accurately classifies dependency, syntax, and database errors."""
    analyzer = ErrorAnalyzer()

    # 1. Missing module
    diag_dep = analyzer.analyze_error("ModuleNotFoundError: No module named 'scipy'")
    assert diag_dep.category == ErrorCategory.DEPENDENCY
    assert "scipy" in diag_dep.missing_packages
    assert diag_dep.requires_confirmation is True

    # 2. Syntax Error
    diag_syn = analyzer.analyze_error("SyntaxError: invalid syntax around line 42")
    assert diag_syn.category == ErrorCategory.SYNTAX

    # 3. Database Connection Failure
    diag_db = analyzer.analyze_error("psycopg2.OperationalError: could not connect to server: Connection refused")
    assert diag_db.category == ErrorCategory.DATABASE


@pytest.mark.asyncio
async def test_registered_coding_tools(sample_python_project):
    """Verify registered coding tools execute and verify cleanly."""
    agent = CodingAgent()
    proj_str = str(sample_python_project)

    inspect_tool = CodingInspectProjectTool(coding_agent=agent)
    search_tool = CodingSearchCodeTool(coding_agent=agent)
    symbol_tool = CodingFindSymbolTool(coding_agent=agent)
    read_tool = CodingReadCodeFileTool(coding_agent=agent)
    patch_tool = CodingApplyPatchTool(coding_agent=agent)
    create_tool = CodingCreateFileTool(coding_agent=agent)
    error_tool = CodingAnalyzeErrorTool(coding_agent=agent)
    git_tool = CodingGitStatusTool(coding_agent=agent)
    diff_tool = CodingGitDiffTool(coding_agent=agent)

    # 1. Inspect
    i_res = await inspect_tool.run(project_path=proj_str)
    assert (await inspect_tool.verify(i_res))["verified"] is True

    # 2. Search
    s_res = await search_tool.run(project_path=proj_str, query="FastAPI")
    assert (await search_tool.verify(s_res))["verified"] is True

    # 3. Find Symbol
    sym_res = await symbol_tool.run(project_path=proj_str, symbol_name="health_check")
    assert (await symbol_tool.verify(sym_res))["verified"] is True

    # 4. Read File
    r_res = await read_tool.run(project_path=proj_str, file_path="main.py")
    assert (await read_tool.verify(r_res))["verified"] is True

    # 5. Create File
    c_res = await create_tool.run(project_path=proj_str, file_path="utils.py", content="def add(a, b):\n    return a + b\n")
    assert (await create_tool.verify(c_res))["verified"] is True

    # 6. Apply Patch
    p_res = await patch_tool.run(
        project_path=proj_str,
        file_path="utils.py",
        target_chunk="    return a + b\n",
        replacement_chunk="    # add two numbers\n    return a + b\n"
    )
    assert (await patch_tool.verify(p_res))["verified"] is True

    # 7. Analyze Error
    err_res = await error_tool.run(error_log="ModuleNotFoundError: No module named 'jwt'")
    assert (await error_tool.verify(err_res))["verified"] is True

    # 8. Git Status
    g_res = await git_tool.run(project_path=proj_str)
    assert (await git_tool.verify(g_res))["verified"] is True

    # 9. Git Diff
    d_res = await diff_tool.run(project_path=proj_str)
    assert (await diff_tool.verify(d_res))["verified"] is True
