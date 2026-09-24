"""
SHIVANI Project Context Models
Structured data models representing user software projects, dependencies,
Git status, documentation summaries, and startup commands.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProjectMetadata(BaseModel):
    name: str = Field(description="Project name or directory identifier")
    path: str = Field(description="Absolute filesystem path to project root")
    git_remote: Optional[str] = Field(default=None, description="Git remote repository URL (e.g. GitHub)")
    languages: List[str] = Field(default_factory=list, description="Primary programming languages detected")
    frameworks: List[str] = Field(default_factory=list, description="Detected frameworks and libraries")
    entry_points: List[str] = Field(default_factory=list, description="Primary runnable entrypoints (e.g. main.py, app.py)")
    readme_summary: str = Field(default="", description="Executive summary extracted from README.md")
    key_features: List[str] = Field(default_factory=list, description="Key features extracted from documentation")
    demo_url: Optional[str] = Field(default=None, description="Live deployment or demonstration URL if found")
    package_manager: Optional[str] = Field(default=None, description="Detected package manager (pip, npm, cargo, etc.)")
    safe_run_command: Optional[str] = Field(default=None, description="Safe startup command verified for local execution")
    last_modified: str = Field(default="", description="Timestamp of last modification")
    git_status: Dict[str, Any] = Field(default_factory=dict, description="Git branch and dirty status")
