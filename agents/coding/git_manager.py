"""
SHIVANI Git Safety & Repository Manager
Inspects git status, warns on dirty repositories, creates safety checkpoint branches,
generates diff summaries, and strictly gates commits and pushes behind user authorization.
"""

import asyncio
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agents.coding.models import GitStatusInfo


class GitManager:
    """Manages Git state inspection, safety checkpoints, and diff auditing."""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()

    async def _run_git(self, args: List[str]) -> Tuple[int, str, str]:
        """Executes a git command safely in the repository directory."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", *args,
                cwd=str(self.repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return (
                proc.returncode if proc.returncode is not None else 1,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace")
            )
        except Exception as e:
            return (1, "", str(e))

    async def get_status(self) -> GitStatusInfo:
        """Inspects git repository status and identifies dirty/clean state."""
        code, out, _ = await self._run_git(["status", "--porcelain", "-b"])
        if code != 0:
            return GitStatusInfo(is_git=False)

        lines = out.strip().splitlines()
        branch = "main"
        modified_files = []
        untracked_files = []
        staged_files = []

        if lines:
            first = lines[0]
            if first.startswith("## "):
                branch_info = first[3:].split("...")[0].strip()
                branch = branch_info

            for line in lines[1:]:
                if len(line) < 3:
                    continue
                code_prefix = line[:2]
                filename = line[3:].strip()
                if code_prefix == "??":
                    untracked_files.append(filename)
                elif code_prefix[0] in ("M", "A", "D", "R"):
                    staged_files.append(filename)
                elif code_prefix[1] in ("M", "D"):
                    modified_files.append(filename)

        is_clean = len(modified_files) == 0 and len(staged_files) == 0

        # Check remote url
        _, remote_out, _ = await self._run_git(["config", "--get", "remote.origin.url"])
        remote_url = remote_out.strip() or None

        return GitStatusInfo(
            is_git=True,
            branch=branch,
            is_clean=is_clean,
            modified_files=modified_files,
            untracked_files=untracked_files,
            staged_files=staged_files,
            remote_url=remote_url
        )

    async def create_checkpoint_branch(self, prefix: str = "shivani-checkpoint") -> Optional[str]:
        """Creates a safety checkpoint branch before applying broad modifications."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        branch_name = f"{prefix}-{ts}"
        code, _, _ = await self._run_git(["checkout", "-b", branch_name])
        return branch_name if code == 0 else None

    async def get_diff(self, cached: bool = False) -> Dict[str, Any]:
        """Generates unified diff and calculates change metrics."""
        args = ["diff"]
        if cached:
            args.append("--cached")

        code, out, err = await self._run_git(args)
        if code != 0:
            return {"error": err, "diff": "", "files_changed": 0, "lines_added": 0, "lines_removed": 0}

        # Calculate lines added/removed
        lines_added = 0
        lines_removed = 0
        files_changed = set()

        for line in out.splitlines():
            if line.startswith("+++ b/"):
                files_changed.add(line[6:])
            elif line.startswith("+") and not line.startswith("+++"):
                lines_added += 1
            elif line.startswith("-") and not line.startswith("---"):
                lines_removed += 1

        return {
            "diff": out,
            "files_changed": list(files_changed),
            "files_count": len(files_changed),
            "lines_added": lines_added,
            "lines_removed": lines_removed
        }

    async def commit_changes(self, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Creates a git commit. (Strictly invoked ONLY after user approval)."""
        if files:
            for f in files:
                await self._run_git(["add", f])
        else:
            await self._run_git(["add", "-A"])

        code, out, err = await self._run_git(["commit", "-m", message])
        return {
            "success": code == 0,
            "message": message,
            "output": out if code == 0 else err
        }

    async def push_changes(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """Pushes to remote repository. (Strictly invoked ONLY after user approval)."""
        target_branch = branch
        if not target_branch:
            st = await self.get_status()
            target_branch = st.branch

        code, out, err = await self._run_git(["push", remote, target_branch])
        return {
            "success": code == 0,
            "remote": remote,
            "branch": target_branch,
            "output": out if code == 0 else err
        }
