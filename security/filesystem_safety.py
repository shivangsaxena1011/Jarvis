"""
SHIVANI Filesystem Safety Guard
Enforces filesystem boundaries, prevents path traversal and symbolic-link escapes,
and validates file operations against authorized directories.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class FilesystemPolicy:
    """Configures allowed directory boundaries and sensitive restricted zones."""

    DEFAULT_ALLOWED_ROOTS: List[str] = [
        os.getcwd(),
        os.path.expanduser("~\\Documents"),
        os.path.expanduser("~\\Downloads"),
        os.path.expanduser("~\\Pictures"),
        os.path.expanduser("~\\Desktop"),
        "c:\\Users\\Project",
    ]

    BLOCKED_SYSTEM_PATHS: List[str] = [
        os.environ.get("WINDIR", "C:\\Windows"),
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        os.path.expanduser("~\\.ssh"),
        os.path.expanduser("~\\.aws"),
        os.path.expanduser("~\\.gnupg"),
        "/etc",
        "/usr",
        "/var",
        "/boot",
    ]


class PathValidator:
    """Validates paths against traversal attempts, junction/symlink escapes, and restricted roots."""

    @classmethod
    def validate_within_boundary(cls, base_dir: Path, target_path: Path) -> Tuple[bool, str]:
        """Validates that target_path does not escape outside base_dir (path traversal check)."""
        try:
            resolved_base = Path(base_dir).resolve()
            resolved_target = Path(target_path).resolve()
            if not str(resolved_target).startswith(str(resolved_base)):
                return False, f"Path traversal detected: {target_path} escapes workspace {base_dir}"
            return True, ""
        except Exception as e:
            return False, f"Path resolution error: {e}"

    def __init__(self, allowed_roots: Optional[List[str]] = None):

        roots = allowed_roots or FilesystemPolicy.DEFAULT_ALLOWED_ROOTS
        self.allowed_roots = [Path(r).resolve() for r in roots if os.path.exists(r) or True]
        self.blocked_paths = [Path(b).resolve() for b in FilesystemPolicy.BLOCKED_SYSTEM_PATHS if b]

    def is_safe_path(self, target_path: str, allow_relative: bool = True) -> Tuple[bool, Optional[Path], str]:
        """
        Resolves real path (following symlinks/junctions) and checks boundaries.
        Returns (is_safe, resolved_path, reason).
        """
        if not target_path or not str(target_path).strip():
            return False, None, "Empty path provided."

        try:
            raw_path = Path(target_path)
            resolved = raw_path.resolve()
        except Exception as e:
            return False, None, f"Failed to resolve path: {e}"

        # 1. Path traversal inspection
        if ".." in raw_path.parts:
            # Check if resolved path is still within an allowed root
            pass

        # 2. Check blocked system directories
        for blocked in self.blocked_paths:
            try:
                resolved.relative_to(blocked)
                return False, resolved, f"Target '{resolved}' is inside restricted system directory '{blocked}'."
            except ValueError:
                pass

        # 3. Check allowed roots
        in_allowed = False
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root)
                in_allowed = True
                break
            except ValueError:
                continue

        if not in_allowed:
            # If not in explicitly allowed roots, check if under current user home directory
            home = Path.home().resolve()
            try:
                resolved.relative_to(home)
                in_allowed = True
            except ValueError:
                pass

        if not in_allowed:
            return False, resolved, f"Path '{resolved}' is outside authorized workspace and user directories."

        return True, resolved, "Path is within authorized boundaries."


class FileOperationGuard:
    """Estimates impact and enforces verification on multi-file operations."""

    @classmethod
    def estimate_impact(cls, operation: str, target_paths: List[str]) -> Dict[str, Any]:
        count = len(target_paths)
        is_mass_operation = count > 5
        is_destructive = operation.lower() in ("delete", "remove", "overwrite", "truncate")

        requires_explicit_approval = is_destructive or is_mass_operation
        return {
            "operation": operation,
            "target_count": count,
            "targets": target_paths[:10],
            "is_mass_operation": is_mass_operation,
            "is_destructive": is_destructive,
            "requires_approval": requires_explicit_approval,
        }
