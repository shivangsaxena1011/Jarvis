"""
SHIVANI Artifact Manager
Organizes all generated professional artifacts in structured, non-polluting locations:
workspace/shivani-artifacts/
├── project/
├── research/
├── presentations/
├── reports/
├── checkpoints/
└── logs/
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone


class ArtifactManager:
    """Manages the creation, retrieval, and organization of generated artifacts."""

    DEFAULT_ROOT = Path("workspace/shivani-artifacts")

    CATEGORIES = ("project", "research", "presentations", "reports", "checkpoints", "logs")

    def __init__(self, root_dir: Optional[Union[str, Path]] = None):
        self.root_dir = Path(root_dir) if root_dir else self.DEFAULT_ROOT
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Creates the artifact directory tree if it does not already exist."""
        self.root_dir.mkdir(parents=True, exist_ok=True)
        for cat in self.CATEGORIES:
            (self.root_dir / cat).mkdir(parents=True, exist_ok=True)

    def get_category_dir(self, category: str) -> Path:
        """Returns the absolute path to a specific artifact category directory."""
        if category not in self.CATEGORIES:
            cat_dir = self.root_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)
            return cat_dir.resolve()
        return (self.root_dir / category).resolve()

    def get_artifact_path(self, category: str, filename: str) -> Path:
        """Resolves target path for an artifact."""
        return self.get_category_dir(category) / filename

    def save_artifact(
        self,
        category: str,
        filename: str,
        content: Union[str, bytes, Dict[str, Any], List[Any]],
        is_binary: bool = False
    ) -> Path:
        """
        Saves an artifact to its dedicated directory.
        Handles text, raw bytes (e.g. PPTX / PDF), and JSON data.
        """
        target_path = self.get_artifact_path(category, filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if is_binary and isinstance(content, bytes):
            target_path.write_bytes(content)
        elif isinstance(content, (dict, list)):
            target_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
        else:
            target_path.write_text(str(content), encoding="utf-8")

        return target_path

    def load_artifact(self, category: str, filename: str, is_json: bool = False) -> Any:
        """Loads an artifact from disk."""
        target_path = self.get_artifact_path(category, filename)
        if not target_path.exists():
            return None

        if is_json:
            try:
                return json.loads(target_path.read_text(encoding="utf-8"))
            except Exception:
                return None
        return target_path.read_text(encoding="utf-8")

    def list_artifacts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists metadata for all stored artifacts."""
        results = []
        categories = [category] if category else self.CATEGORIES

        for cat in categories:
            cat_dir = self.get_category_dir(cat)
            if not cat_dir.exists():
                continue
            for item in cat_dir.iterdir():
                if item.is_file():
                    stat = item.stat()
                    results.append({
                        "name": item.name,
                        "category": cat,
                        "path": str(item.resolve()),
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    })
        return results

    def save_checkpoint(self, checkpoint_id: str, stage: str, data: Dict[str, Any]) -> Path:
        """Persists a long-running workflow state checkpoint."""
        payload = {
            "checkpoint_id": checkpoint_id,
            "stage": stage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        filename = f"{checkpoint_id}_{stage}.json"
        return self.save_artifact("checkpoints", filename, payload)

    def load_checkpoint(self, checkpoint_id: str, stage: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Loads the most recent checkpoint or a specific stage checkpoint."""
        ckpt_dir = self.get_category_dir("checkpoints")
        if not ckpt_dir.exists():
            return None

        candidates = []
        for item in ckpt_dir.glob(f"{checkpoint_id}_*.json"):
            if stage and not item.name.endswith(f"_{stage}.json"):
                continue
            candidates.append(item)

        if not candidates:
            return None

        # Sort by modification time to get latest
        candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        try:
            return json.loads(candidates[0].read_text(encoding="utf-8"))
        except Exception:
            return None
