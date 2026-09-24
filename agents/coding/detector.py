"""
SHIVANI Project Detector
Inspects actual repository files to deduce languages, frameworks, package managers,
entry points, test runners, build systems, databases, and configuration.
Never assumes the stack without physical file verification.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from agents.coding.models import ProjectSpec


class ProjectDetector:
    """Accurately discovers software stack metadata from filesystem inspection."""

    def detect_project(self, project_dir: Path) -> ProjectSpec:
        """Inspects directory and produces a comprehensive ProjectSpec."""
        p = Path(project_dir).resolve()
        name = p.name

        languages: Set[str] = set()
        frameworks: Set[str] = set()
        package_manager: Optional[str] = None
        entry_points: List[str] = []
        test_framework: Optional[str] = None
        build_system: Optional[str] = None
        database: Optional[str] = None
        safe_run_command: Optional[str] = None
        test_command: Optional[str] = None
        build_command: Optional[str] = None
        env_vars_detected: List[str] = []

        # 1. Inspect Python
        pyproject = p / "pyproject.toml"
        requirements = p / "requirements.txt"
        setup_py = p / "setup.py"
        has_python_files = any(p.glob("*.py")) or any(p.glob("*/*.py"))

        if pyproject.exists():
            m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', pyproject.read_text(encoding="utf-8", errors="ignore"))
            if m:
                name = m.group(1)

        if pyproject.exists() or requirements.exists() or setup_py.exists() or has_python_files:
            languages.add("Python")
            package_manager = "uv" if (p / "uv.lock").exists() else ("poetry" if (p / "poetry.lock").exists() else "pip")

            # Check dependencies content
            dep_text = ""
            if pyproject.exists():
                dep_text += pyproject.read_text(encoding="utf-8", errors="ignore")
            if requirements.exists():
                dep_text += requirements.read_text(encoding="utf-8", errors="ignore")

            lower_dep = dep_text.lower()
            if "fastapi" in lower_dep:
                frameworks.add("FastAPI")
                safe_run_command = "uvicorn main:app --reload" if (p / "main.py").exists() else "python -m uvicorn"
            elif "flask" in lower_dep:
                frameworks.add("Flask")
                safe_run_command = "flask run"
            elif "django" in lower_dep:
                frameworks.add("Django")
                safe_run_command = "python manage.py runserver"

            if "pytest" in lower_dep or (p / "pytest.ini").exists():
                test_framework = "pytest"
                test_command = "pytest"
            else:
                test_framework = "unittest"
                test_command = "python -m unittest discover"

            # Entry points
            for ep in ["main.py", "app.py", "run.py", "server.py", "manage.py"]:
                if (p / ep).exists():
                    entry_points.append(ep)
                    if not safe_run_command:
                        safe_run_command = f"python {ep}"

        # 2. Inspect Node.js / TypeScript / JavaScript
        package_json = p / "package.json"
        if package_json.exists():
            languages.add("JavaScript")
            try:
                pkg_data = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
                scripts = pkg_data.get("scripts", {})
                deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}

                # Package manager detection
                if (p / "pnpm-lock.yaml").exists():
                    package_manager = "pnpm"
                elif (p / "yarn.lock").exists():
                    package_manager = "yarn"
                elif (p / "bun.lockb").exists():
                    package_manager = "bun"
                else:
                    package_manager = "npm"

                # TypeScript
                if (p / "tsconfig.json").exists() or "typescript" in deps:
                    languages.add("TypeScript")

                # Frameworks
                if "next" in deps:
                    frameworks.add("Next.js")
                    frameworks.add("React")
                    build_system = f"{package_manager} run build"
                    build_command = build_system
                    safe_run_command = f"{package_manager} run dev"
                elif "react" in deps:
                    frameworks.add("React")
                    safe_run_command = f"{package_manager} start"
                elif "vue" in deps:
                    frameworks.add("Vue")
                elif "express" in deps:
                    frameworks.add("Express")
                    safe_run_command = f"{package_manager} start"
                elif "nestjs" in deps or "@nestjs/core" in deps:
                    frameworks.add("NestJS")
                    safe_run_command = f"{package_manager} run start:dev"

                # Test Framework
                if "jest" in deps or "jest" in scripts:
                    test_framework = "jest"
                    test_command = f"{package_manager} test"
                elif "vitest" in deps or "vitest" in scripts:
                    test_framework = "vitest"
                    test_command = f"{package_manager} test"
                elif "test" in scripts:
                    test_framework = "npm-test"
                    test_command = f"{package_manager} test"

                # Check scripts for run/build
                if "dev" in scripts and not safe_run_command:
                    safe_run_command = f"{package_manager} run dev"
                elif "start" in scripts and not safe_run_command:
                    safe_run_command = f"{package_manager} start"

                if "build" in scripts and not build_command:
                    build_command = f"{package_manager} run build"

                # Entry points
                main_file = pkg_data.get("main")
                if main_file and (p / main_file).exists():
                    entry_points.append(main_file)
            except Exception:
                pass

        # 3. Inspect Rust
        if (p / "Cargo.toml").exists():
            languages.add("Rust")
            package_manager = "cargo"
            build_system = "cargo build"
            build_command = "cargo build"
            test_framework = "cargo test"
            test_command = "cargo test"
            safe_run_command = "cargo run"
            if (p / "src" / "main.rs").exists():
                entry_points.append("src/main.rs")

        # 4. Inspect Go
        if (p / "go.mod").exists():
            languages.add("Go")
            package_manager = "go"
            test_framework = "go test"
            test_command = "go test ./..."
            safe_run_command = "go run ."
            if (p / "main.go").exists():
                entry_points.append("main.go")

        # 5. Inspect Databases
        for check_file in [p / "requirements.txt", p / "pyproject.toml", p / "package.json", p / "docker-compose.yml"]:
            if check_file.exists():
                content = check_file.read_text(encoding="utf-8", errors="ignore").lower()
                if "postgresql" in content or "psycopg" in content or "pg" in content:
                    database = "PostgreSQL"
                elif "sqlite" in content or "sqlite3" in content:
                    database = "SQLite"
                elif "mongodb" in content or "pymongo" in content or "mongoose" in content:
                    database = "MongoDB"
                elif "redis" in content:
                    database = "Redis"

        # 6. Inspect Environment Variables (.env / .env.example) - Strictly names only, no values!
        for env_file in [p / ".env", p / ".env.example", p / ".env.local"]:
            if env_file.exists():
                for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        var_name = line.split("=", 1)[0].strip()
                        if var_name and var_name not in env_vars_detected:
                            env_vars_detected.append(var_name)

        # 7. Git Presence
        has_git = (p / ".git").exists()

        return ProjectSpec(
            name=name,
            path=str(p),
            languages=sorted(list(languages)) if languages else ["Unknown"],
            frameworks=sorted(list(frameworks)),
            package_manager=package_manager,
            entry_points=entry_points,
            build_system=build_system,
            test_framework=test_framework,
            database=database,
            has_git=has_git,
            safe_run_command=safe_run_command,
            test_command=test_command,
            build_command=build_command,
            env_vars_detected=env_vars_detected
        )
