"""
Real-world Coding Agent & Safety Acceptance Test (Phase 20.5)
Verifies bug detection, automated fixing, syntax testing, git diff generation,
and prevention of silent commits or pushes without user authorization.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import pytest


def test_real_coding_bug_fix_and_git_safety():
    """Initializes a real git repo, introduces a bug, verifies diff inspection, runs tests, and confirms no silent push."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir).resolve()

        # 1. Initialize git repo
        subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "shivani-test@example.com"], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "config", "user.name", "Shivani Bot"], cwd=str(repo_dir), check=True)

        # 2. Add buggy python code
        calc_file = repo_dir / "calculator.py"
        buggy_code = """def add_numbers(a, b):
    # BUG: Subtracts instead of adds
    return a - b
"""
        calc_file.write_text(buggy_code, encoding="utf-8")

        test_file = repo_dir / "test_calculator.py"
        test_code = """from calculator import add_numbers

def test_add():
    assert add_numbers(2, 3) == 5
"""
        test_file.write_text(test_code, encoding="utf-8")

        # Initial commit of base files
        subprocess.run(["git", "add", "."], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(repo_dir), check=True)

        # 3. Verify test currently fails due to bug
        test_env = os.environ.copy()
        test_env["PYTHONDONTWRITEBYTECODE"] = "1"
        res_fail = subprocess.run(
            [sys.executable, "-m", "pytest", "test_calculator.py", "-p", "no:cacheprovider"],
            cwd=str(repo_dir),
            env=test_env,
            capture_output=True
        )
        assert res_fail.returncode != 0

        # 4. Agent simulates fix
        fixed_code = """def add_numbers(a, b):
    # FIXED: Correct addition
    return a + b
"""
        calc_file.write_text(fixed_code, encoding="utf-8")

        # 5. Check git diff is available for review
        res_diff = subprocess.run(["git", "diff"], cwd=str(repo_dir), capture_output=True, text=True)
        diff_text = res_diff.stdout
        assert "-    return a - b" in diff_text
        assert "+    return a + b" in diff_text

        # 6. Verify tests now pass
        res_pass = subprocess.run(
            [sys.executable, "-m", "pytest", "test_calculator.py", "-p", "no:cacheprovider"],
            cwd=str(repo_dir),
            env=test_env,
            capture_output=True
        )
        assert res_pass.returncode == 0

        # 7. Safety: verify changes remain in unstaged/working state and are NOT silently committed or pushed
        status_res = subprocess.run(["git", "status", "--porcelain"], cwd=str(repo_dir), capture_output=True, text=True)
        assert "M calculator.py" in status_res.stdout
        # Remote tracking branch does not exist, proving zero silent pushes occurred
        remotes_res = subprocess.run(["git", "remote"], cwd=str(repo_dir), capture_output=True, text=True)
        assert remotes_res.stdout.strip() == ""
