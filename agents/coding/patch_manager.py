"""
SHIVANI Patch Manager
Applies targeted modifications, computes unified diffs, tracks changes,
and performs pre-write syntax validation to prevent syntax breakages.
"""

import ast
import difflib
from pathlib import Path
from typing import Optional, Tuple

from agents.coding.models import PatchResult


class PatchManager:
    """Handles precision code edits and diff auditing."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()

    def generate_diff(self, original_text: str, new_text: str, file_path: str = "") -> Tuple[str, int, int]:
        """Calculates a clean unified diff and count added/removed lines."""
        orig_lines = original_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff_lines = list(difflib.unified_diff(
            orig_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}"
        ))
        diff_str = "".join(diff_lines)

        added = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
        return diff_str, added, removed

    def apply_replacement(
        self,
        rel_file_path: str,
        target_chunk: str,
        replacement_chunk: str
    ) -> PatchResult:
        """
        Replaces target_chunk with replacement_chunk in the given file.
        Verifies Python syntax before persisting.
        """
        file_abs = self.project_path / rel_file_path
        if not file_abs.exists():
            return PatchResult(file_path=rel_file_path, success=False, error=f"File does not exist: {rel_file_path}")

        try:
            original_content = file_abs.read_text(encoding="utf-8")
        except Exception as e:
            return PatchResult(file_path=rel_file_path, success=False, error=f"Failed to read file: {e}")

        if target_chunk not in original_content:
            return PatchResult(
                file_path=rel_file_path,
                success=False,
                error="Target content was not found in file. Ensure exact whitespace and line match."
            )

        new_content = original_content.replace(target_chunk, replacement_chunk, 1)

        # Syntax validation for Python files
        if rel_file_path.endswith(".py"):
            try:
                ast.parse(new_content)
            except SyntaxError as se:
                return PatchResult(
                    file_path=rel_file_path,
                    success=False,
                    error=f"Syntax error after replacement at line {se.lineno}: {se.msg}"
                )

        diff_str, added, removed = self.generate_diff(original_content, new_content, rel_file_path)

        try:
            file_abs.write_text(new_content, encoding="utf-8")
            return PatchResult(
                file_path=rel_file_path,
                success=True,
                unified_diff=diff_str,
                lines_added=added,
                lines_removed=removed
            )
        except Exception as e:
            return PatchResult(file_path=rel_file_path, success=False, error=f"Failed to write file: {e}")

    def create_new_file(self, rel_file_path: str, content: str) -> PatchResult:
        """Safely creates a new file within the repository."""
        file_abs = self.project_path / rel_file_path
        if file_abs.exists():
            return PatchResult(file_path=rel_file_path, success=False, error=f"File already exists: {rel_file_path}")

        # Syntax check if Python
        if rel_file_path.endswith(".py"):
            try:
                ast.parse(content)
            except SyntaxError as se:
                return PatchResult(
                    file_path=rel_file_path,
                    success=False,
                    error=f"Syntax error in new file at line {se.lineno}: {se.msg}"
                )

        try:
            file_abs.parent.mkdir(parents=True, exist_ok=True)
            file_abs.write_text(content, encoding="utf-8")
            diff_str, added, removed = self.generate_diff("", content, rel_file_path)
            return PatchResult(
                file_path=rel_file_path,
                success=True,
                unified_diff=diff_str,
                lines_added=added,
                lines_removed=removed
            )
        except Exception as e:
            return PatchResult(file_path=rel_file_path, success=False, error=f"Failed to create file: {e}")
