"""
SHIVANI Code Search & Repository Analyzer
Provides targeted semantic & textual search, symbol location, focused context assembly,
and strict environment variable / credential redaction.
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agents.coding.models import CodeContext


SECRET_PATTERN = re.compile(
    r'(?i)(api[_-]?key|token|secret|password|passwd|private[_-]?key|auth[_-]?key|client[_-]?secret)\s*[:=]\s*["\']?([^"\'\s\r\n]{4,})["\']?'
)


class CodeSearch:
    """Fast, scoped file and symbol search within a project directory."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()

    def find_files(self, pattern: str = "*", max_results: int = 50) -> List[str]:
        """Finds matching files ignoring noise directories."""
        results = []
        for p in self.project_path.rglob(pattern):
            if not p.is_file():
                continue
            rel = p.relative_to(self.project_path).as_posix()
            if any(seg in rel.split("/") for seg in [".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"]):
                continue
            results.append(rel)
            if len(results) >= max_results:
                break
        return results

    def search_text(self, query: str, file_pattern: Optional[str] = None, max_results: int = 30) -> List[Dict[str, Any]]:
        """Textual search returning file, line number, and matching line content."""
        matches = []
        target_files = self.find_files(file_pattern or "*")

        for rel_path in target_files:
            file_abs = self.project_path / rel_path
            try:
                content = file_abs.read_text(encoding="utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    if query.lower() in line.lower():
                        matches.append({
                            "file": rel_path,
                            "line": line_idx,
                            "content": line.strip()
                        })
                        if len(matches) >= max_results:
                            return matches
            except Exception:
                continue
        return matches

    def find_symbol(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Finds function or class definitions across the codebase."""
        results = []
        python_files = self.find_files("*.py")

        for rel_path in python_files:
            file_abs = self.project_path / rel_path
            try:
                tree = ast.parse(file_abs.read_text(encoding="utf-8", errors="ignore"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if symbol_name.lower() in node.name.lower():
                            results.append({
                                "file": rel_path,
                                "name": node.name,
                                "type": "class" if isinstance(node, ast.ClassDef) else "function",
                                "line": node.lineno
                            })
            except Exception:
                continue
        return results

    def read_file(self, rel_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> Tuple[bool, str]:
        """Reads file content with optional slice boundaries and secret redaction."""
        file_abs = self.project_path / rel_path
        if not file_abs.exists() or not file_abs.is_file():
            return False, f"File not found: {rel_path}"

        try:
            raw_content = file_abs.read_text(encoding="utf-8", errors="replace")
            # Redact secrets
            redacted_content = SECRET_PATTERN.sub(r'\1="[REDACTED]"', raw_content)

            lines = redacted_content.splitlines()
            if start_line is not None or end_line is not None:
                s = max(0, (start_line - 1) if start_line else 0)
                e = min(len(lines), end_line if end_line else len(lines))
                return True, "\n".join(lines[s:e])

            return True, redacted_content
        except Exception as e:
            return False, str(e)


class CodeAnalyzer:
    """Extracts focused contextual subsets for specific tasks to avoid whole-repo LLM dumping."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.search = CodeSearch(self.project_path)

    def assemble_context_for_task(self, query: str, max_files: int = 5) -> CodeContext:
        """Collects relevant files and symbol definitions matching the task keywords."""
        keywords = [w.lower() for w in re.findall(r'\b[A-Za-z_][A-Za-z0-9_]+\b', query) if len(w) > 3]
        matched_files = set()
        relevant_symbols = []

        # Find files matching keywords
        for kw in keywords:
            for m in self.search.search_text(kw, max_results=10):
                matched_files.add(m["file"])
                if len(matched_files) >= max_files:
                    break
            for sym in self.search.find_symbol(kw):
                matched_files.add(sym["file"])
                relevant_symbols.append(f"{sym['type']} {sym['name']} in {sym['file']}:{sym['line']}")

        # Ensure README or main entry is included if nothing found
        if not matched_files:
            for default_file in ["README.md", "main.py", "app.py", "package.json"]:
                if (self.project_path / default_file).exists():
                    matched_files.add(default_file)

        file_contents = {}
        for f in list(matched_files)[:max_files]:
            success, text = self.search.read_file(f)
            if success:
                # Cap file size for context
                file_contents[f] = text[:4000]

        summary = f"Identified {len(matched_files)} relevant files for task: '{query}'."
        return CodeContext(
            target_files=list(file_contents.keys()),
            file_contents=file_contents,
            relevant_symbols=relevant_symbols[:10],
            architecture_summary=summary
        )

    def redact_secrets(self, text: str) -> str:
        """Utility method to sanitize any string containing credentials."""
        return SECRET_PATTERN.sub(r'\1="[REDACTED]"', text)
