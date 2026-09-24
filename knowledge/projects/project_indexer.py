"""
SHIVANI Project Indexer
Discovers project root, Git metadata, tech stack, dependencies,
entry points, test runners, and architectural blueprints.
"""

import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from knowledge.models import (
    GraphEdge,
    KnowledgeItem,
    KnowledgeType,
    ProjectProfile,
    RelationType,
)
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


class ProjectIndexer:
    """Discovers and structures comprehensive project profiles."""

    def __init__(self, store: Optional[SQLiteKnowledgeStore] = None):
        self.store = store

    def discover_project(self, root_dir: str) -> ProjectProfile:
        """Inspects directory structure to construct a rich ProjectProfile."""
        root = Path(root_dir).resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"Directory not found: {root_dir}")

        name = root.name
        version: Optional[str] = "0.1.0"
        languages: List[str] = []
        frameworks: List[str] = []
        package_managers: List[str] = []
        entry_points: List[str] = []
        test_frameworks: List[str] = []
        key_docs: List[str] = []
        repo_url: Optional[str] = None
        git_branch: Optional[str] = None

        # Check Git
        git_head = root / ".git" / "HEAD"
        if git_head.is_file():
            try:
                head_content = git_head.read_text(encoding="utf-8").strip()
                if head_content.startswith("ref: refs/heads/"):
                    git_branch = head_content.replace("ref: refs/heads/", "")
            except Exception:
                pass

        # Check Python configs
        pyproject = root / "pyproject.toml"
        if pyproject.is_file():
            languages.append("Python")
            package_managers.append("uv/pip")
            try:
                content = pyproject.read_text(encoding="utf-8", errors="ignore")
                m_name = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if m_name:
                    name = m_name.group(1)
                m_ver = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if m_ver:
                    version = m_ver.group(1)
                if "fastapi" in content.lower():
                    frameworks.append("FastAPI")
                if "pytest" in content.lower():
                    test_frameworks.append("pytest")
                if "playwright" in content.lower():
                    frameworks.append("Playwright")
            except Exception:
                pass

        reqs = root / "requirements.txt"
        if reqs.is_file() and "Python" not in languages:
            languages.append("Python")
            package_managers.append("pip")

        # Check Node / JS / TS
        pkg_json = root / "package.json"
        if pkg_json.is_file():
            package_managers.append("npm")
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
                if not name or name == root.name:
                    name = data.get("name", name)
                version = data.get("version", version)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "react" in deps:
                    frameworks.append("React")
                if "next" in deps:
                    frameworks.append("Next.js")
                if "typescript" in deps or (root / "tsconfig.json").is_file():
                    languages.append("TypeScript")
                else:
                    languages.append("JavaScript")
                if "jest" in deps or "vitest" in deps:
                    test_frameworks.append("jest/vitest")
            except Exception:
                pass

        # Common entry points
        for ep in ("main.py", "app.py", "run.py", "server.py", "index.js", "index.ts", "server.ts"):
            if (root / ep).is_file():
                entry_points.append(ep)

        # Architectural documentation
        for doc_name in (
            "README.md",
            "ARCHITECTURE.md",
            "PRD.md",
            "DESIGN.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
        ):
            if (root / doc_name).is_file():
                key_docs.append(str(root / doc_name))

        # Check docs/ directory
        docs_dir = root / "docs"
        if docs_dir.is_dir():
            for doc_file in docs_dir.glob("*.md"):
                key_docs.append(str(doc_file))

        # Architecture summary: read first 1000 chars of README or ARCHITECTURE.md
        arch_overview = ""
        for arch_file in (root / "ARCHITECTURE.md", root / "README.md"):
            if arch_file.is_file():
                try:
                    txt = arch_file.read_text(encoding="utf-8", errors="ignore")
                    arch_overview = txt[:1200].strip()
                    break
                except Exception:
                    pass

        profile = ProjectProfile(
            id=f"proj_{name.lower().replace(' ', '_').replace('-', '_')}",
            name=name,
            root_path=str(root),
            version=version,
            repository_url=repo_url,
            git_branch=git_branch,
            languages=list(dict.fromkeys(languages)),
            frameworks=list(dict.fromkeys(frameworks)),
            package_managers=list(dict.fromkeys(package_managers)),
            entry_points=entry_points,
            test_frameworks=test_frameworks,
            architecture_overview=arch_overview,
            key_documents=key_docs,
            key_symbols_count=0,
            total_files_indexed=0,
        )

        # If store is provided, save project item and graph edges
        if self.store:
            item = KnowledgeItem(
                id=profile.id,
                type=KnowledgeType.PROJECT,
                title=profile.name,
                content=profile.architecture_overview or f"Project {profile.name} at {profile.root_path}",
                summary=f"Project {profile.name} (v{profile.version}) using {', '.join(profile.languages + profile.frameworks)}",
                source=profile.root_path,
                project_id=profile.id,
                metadata=profile.model_dump(),
            )
            self.store.save_item(item)

            # Link technologies
            edges: List[GraphEdge] = []
            for tech in profile.frameworks + profile.languages:
                edges.append(
                    GraphEdge(
                        source_id=profile.id,
                        target_id=f"tech_{tech.lower()}",
                        relation_type=RelationType.USES_TECHNOLOGY,
                        weight=1.0,
                        metadata={"technology": tech},
                    )
                )
            if edges:
                self.store.save_edges(edges)

        return profile
