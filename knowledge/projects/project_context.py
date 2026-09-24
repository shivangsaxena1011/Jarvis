"""
SHIVANI Project Context Formatter
Assembles project intelligence into high-signal Markdown prompts for LLM agents.
"""

from typing import Any, Dict, List, Optional
from knowledge.models import ProjectProfile


class ProjectContext:
    """Formats and summarizes ProjectProfile for consumption by agent prompts."""

    @classmethod
    def format_for_prompt(cls, profile: ProjectProfile, max_chars: int = 2500) -> str:
        """Constructs a clean, structured Markdown context snippet."""
        lines = [
            f"# Project: {profile.name} (v{profile.version or '0.1.0'})",
            f"- **Root Path**: `{profile.root_path}`",
        ]
        if profile.git_branch:
            lines.append(f"- **Git Branch**: `{profile.git_branch}`")
        if profile.languages:
            lines.append(f"- **Languages**: {', '.join(profile.languages)}")
        if profile.frameworks:
            lines.append(f"- **Frameworks**: {', '.join(profile.frameworks)}")
        if profile.package_managers:
            lines.append(f"- **Package Managers**: {', '.join(profile.package_managers)}")
        if profile.entry_points:
            lines.append(f"- **Entry Points**: {', '.join(f'`{e}`' for e in profile.entry_points)}")
        if profile.test_frameworks:
            lines.append(f"- **Test Frameworks**: {', '.join(profile.test_frameworks)}")

        if profile.architecture_overview:
            lines.append("\n## Architectural Blueprint")
            # Truncate blueprint if too long
            bp = profile.architecture_overview[:1000].strip()
            lines.append(bp)

        if profile.key_documents:
            lines.append("\n## Key Architectural Documents")
            for doc in profile.key_documents[:8]:
                lines.append(f"- `{doc}`")

        full_text = "\n".join(lines)
        if len(full_text) > max_chars:
            return full_text[:max_chars] + "\n... [truncated]"
        return full_text
