"""
SHIVANI Local Project Indexer
Discovers, analyzes, and indexes software projects within authorized project roots.
Extracts README summaries, frameworks, Git remotes, and safe run commands.
"""

import os
import re
import difflib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import get_settings
from core.projects.models import ProjectMetadata


class ProjectIndexer:
    """Manages discovery and structured metadata caching for local user projects."""

    def __init__(self, authorized_roots: Optional[List[str]] = None):
        self.settings = get_settings()
        roots = authorized_roots if authorized_roots is not None else self.settings.AUTHORIZED_PROJECT_ROOTS
        if not roots:
            # Default to current directory and parent directory if authorized
            cwd = Path.cwd().resolve()
            roots = [str(cwd), str(cwd.parent)]
        self.authorized_roots = [Path(r).resolve() for r in roots]
        self._index: Dict[str, ProjectMetadata] = {}
        self._projects_cache = self._index

    def scan_all(self, max_depth: int = 2) -> List[ProjectMetadata]:
        """Scans all authorized project roots and builds the project index."""
        projects = []
        for root in self.authorized_roots:
            if not root.exists() or not root.is_dir():
                continue
            
            # Check if root itself is a project
            if self._is_project_dir(root):
                meta = self.analyze_project(root)
                projects.append(meta)
                self._index[meta.name.lower()] = meta
                continue

            # Otherwise scan subdirectories up to max_depth
            try:
                for entry in root.iterdir():
                    if entry.is_dir() and not entry.name.startswith((".", "_", "venv", ".venv", "node_modules")):
                        if self._is_project_dir(entry):
                            meta = self.analyze_project(entry)
                            projects.append(meta)
                            self._index[meta.name.lower()] = meta
            except Exception:
                continue

        return projects

    def _is_project_dir(self, directory: Path) -> bool:
        """Determines if a directory represents a software project."""
        indicators = [
            ".git",
            "pyproject.toml",
            "requirements.txt",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "README.md",
            "readme.md"
        ]
        return any((directory / ind).exists() for ind in indicators)

    def analyze_project(self, project_path: Path) -> ProjectMetadata:
        """Inspects project structure, documentation, and configuration."""
        name = project_path.name
        git_remote = self._extract_git_remote(project_path)
        readme_summary, key_features, demo_url = self._analyze_readme(project_path)
        languages, frameworks, pkg_manager = self._detect_stack(project_path)
        entry_points = self._detect_entry_points(project_path)
        safe_cmd = self._determine_safe_run_command(project_path, pkg_manager, entry_points, frameworks)

        last_mod = ""
        try:
            mtime = project_path.stat().st_mtime
            last_mod = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        except Exception:
            pass

        meta = ProjectMetadata(
            name=name,
            path=str(project_path.resolve()),
            git_remote=git_remote,
            languages=languages,
            frameworks=frameworks,
            entry_points=entry_points,
            readme_summary=readme_summary,
            key_features=key_features,
            demo_url=demo_url,
            package_manager=pkg_manager,
            safe_run_command=safe_cmd,
            last_modified=last_mod,
            git_status={"is_git_repo": (project_path / ".git").exists()}
        )
        self._index[name.lower()] = meta
        return meta

    def find_project(self, query: str) -> Optional[ProjectMetadata]:
        """Finds the best matching project by name or keywords."""
        if not self._index:
            self.scan_all()

        query_lower = query.lower().strip()
        # Direct exact match
        if query_lower in self._index:
            return self._index[query_lower]

        # Clean query terms
        clean_q = re.sub(r"\b(project|repo|repository|mere|mera|find|locate|check|for|the)\b", "", query_lower).strip()

        best_meta = None
        best_score = -1.0

        for name, meta in self._index.items():
            # Exact substring
            if clean_q and (clean_q in name or name in clean_q):
                score = 0.85 + (len(clean_q) / max(len(name), 1)) * 0.15
            else:
                score = difflib.SequenceMatcher(None, clean_q or query_lower, name).ratio()
            
            # Boost if search terms appear in README summary
            if clean_q and clean_q in meta.readme_summary.lower():
                score += 0.2

            if score > best_score:
                best_score = score
                best_meta = meta

        if best_score > 0.4:
            return best_meta

        return None

    def list_projects(self) -> List[ProjectMetadata]:
        if not self._index:
            self.scan_all()
        return list(self._index.values())

    def _extract_git_remote(self, project_path: Path) -> Optional[str]:
        git_config = project_path / ".git" / "config"
        if git_config.exists() and git_config.is_file():
            try:
                content = git_config.read_text(encoding="utf-8", errors="ignore")
                match = re.search(r'url\s*=\s*(https://[^\s]+|git@[^\s]+)', content)
                if match:
                    url = match.group(1).strip()
                    if url.endswith(".git"):
                        url = url[:-4]
                    return url
            except Exception:
                pass
        return None

    def _analyze_readme(self, project_path: Path) -> tuple[str, List[str], Optional[str]]:
        readme_file = None
        for cand in ["README.md", "readme.md", "README.txt", "readme.txt"]:
            p = project_path / cand
            if p.exists():
                readme_file = p
                break

        if not readme_file:
            return "", [], None

        try:
            text = readme_file.read_text(encoding="utf-8", errors="ignore")
            # Extract demo URL if mentioned
            demo_match = re.search(r'(?:demo|live|app|deployment):\s*(https://[^\s\)]+)', text, re.IGNORECASE)
            demo_url = demo_match.group(1).strip() if demo_match else None

            # Extract features
            features = []
            for line in text.splitlines():
                line_str = line.strip()
                if line_str.startswith(("- ", "* ", "1. ", "2. ", "3. ")) and len(line_str) > 5:
                    clean_line = re.sub(r"^[-*\d.]+\s*", "", line_str)
                    if len(clean_line) < 120:
                        features.append(clean_line)
                if len(features) >= 5:
                    break

            # Strip Markdown headers and markup for summary snippet
            clean_lines = [l for l in text.splitlines() if not l.startswith("#") and len(l.strip()) > 20]
            summary = " ".join(clean_lines[:3])[:400].strip()

            return summary, features, demo_url
        except Exception:
            return "", [], None

    def _detect_stack(self, project_path: Path) -> tuple[List[str], List[str], Optional[str]]:
        languages = []
        frameworks = []
        pkg_manager = None

        # Python
        if (project_path / "requirements.txt").exists() or (project_path / "pyproject.toml").exists() or any(project_path.glob("*.py")):
            languages.append("Python")
            pkg_manager = "pip"
            reqs = ""
            for p in [project_path / "requirements.txt", project_path / "pyproject.toml"]:
                if p.exists():
                    try:
                        reqs += " " + p.read_text(encoding="utf-8", errors="ignore").lower()
                    except Exception:
                        pass
            if "streamlit" in reqs:
                frameworks.append("Streamlit")
            if "fastapi" in reqs:
                frameworks.append("FastAPI")
            if "flask" in reqs:
                frameworks.append("Flask")
            if "django" in reqs:
                frameworks.append("Django")
            if "torch" in reqs or "pytorch" in reqs:
                frameworks.append("PyTorch")
            if "scikit-learn" in reqs or "sklearn" in reqs:
                frameworks.append("Scikit-Learn")

        # JavaScript / TypeScript
        pkg_json = project_path / "package.json"
        if pkg_json.exists():
            pkg_manager = "npm"
            if any(project_path.glob("*.ts")) or (project_path / "tsconfig.json").exists():
                languages.append("TypeScript")
            else:
                languages.append("JavaScript")
            try:
                pj_text = pkg_json.read_text(encoding="utf-8", errors="ignore").lower()
                if "react" in pj_text:
                    frameworks.append("React")
                if "next" in pj_text:
                    frameworks.append("Next.js")
                if "vue" in pj_text:
                    frameworks.append("Vue")
                if "express" in pj_text:
                    frameworks.append("Express")
            except Exception:
                pass

        # Rust
        if (project_path / "Cargo.toml").exists():
            languages.append("Rust")
            pkg_manager = "cargo"

        # Go
        if (project_path / "go.mod").exists():
            languages.append("Go")
            pkg_manager = "go"

        return languages, frameworks, pkg_manager

    def _detect_entry_points(self, project_path: Path) -> List[str]:
        candidates = ["main.py", "app.py", "server.py", "run.py", "index.js", "index.ts", "src/main.rs", "main.go"]
        found = []
        for c in candidates:
            if (project_path / c).exists():
                found.append(c)
        return found

    def _determine_safe_run_command(
        self,
        project_path: Path,
        pkg_manager: Optional[str],
        entry_points: List[str],
        frameworks: List[str]
    ) -> Optional[str]:
        if "Streamlit" in frameworks and "app.py" in entry_points:
            return "streamlit run app.py"
        if "FastAPI" in frameworks and ("main.py" in entry_points or "app.py" in entry_points):
            entry = "main" if "main.py" in entry_points else "app"
            return f"uvicorn {entry}:app --reload"
        if "Python" in pkg_manager or pkg_manager == "pip":
            if "main.py" in entry_points:
                return "python main.py"
            if "app.py" in entry_points:
                return "python app.py"
        if pkg_manager == "npm":
            return "npm start"
        if pkg_manager == "cargo":
            return "cargo run"
        return None
