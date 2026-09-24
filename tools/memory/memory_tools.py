"""
SHIVANI Memory Tools
Exposes memory operations: preferences lookup/setting, keyword searching,
provenance explanation, and forgetting.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from memory.manager import MemoryManager
from memory.models import MemoryCategory, MemoryScope


class MemoryGetPreferenceArgs(BaseModel):
    key: str = Field(description="Preference key name, e.g. 'preferred_browser' or 'preferred_theme'")
    project_id: Optional[str] = Field(default=None, description="Optional project context ID")
    device_id: Optional[str] = Field(default=None, description="Optional device context ID")
    default: Optional[Any] = Field(default=None, description="Default value if not found")


class MemoryGetPreferenceTool(BaseTool):
    name = "memory.get_preference"
    description = "Retrieves a user preference considering device and project overrides with fallback to global."
    permission_level = RiskLevel.SAFE
    args_schema = MemoryGetPreferenceArgs
    timeout = 10.0

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        super().__init__()
        self.memory = memory_manager or MemoryManager()

    async def run(
        self,
        key: str,
        project_id: Optional[str] = None,
        device_id: Optional[str] = None,
        default: Optional[Any] = None,
    ) -> Dict[str, Any]:
        val = self.memory.get_preference(
            key=key,
            project_id=project_id,
            device_id=device_id,
            default=default,
        )
        return {"key": key, "value": val, "found": val is not None}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True}


class MemorySetPreferenceArgs(BaseModel):
    key: str = Field(description="Preference key name")
    value: Any = Field(description="Preference value to store")
    scope: str = Field(default="global", description="Scope: global | project | device")
    scope_id: Optional[str] = Field(default=None, description="Identifier for project or device scope")
    explanation: Optional[str] = Field(default=None, description="Context rationale for this preference")


class MemorySetPreferenceTool(BaseTool):
    name = "memory.set_preference"
    description = "Saves an explicit user preference with automatic secret redaction."
    permission_level = RiskLevel.SAFE
    args_schema = MemorySetPreferenceArgs
    timeout = 10.0

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        super().__init__()
        self.memory = memory_manager or MemoryManager()

    async def run(
        self,
        key: str,
        value: Any,
        scope: str = "global",
        scope_id: Optional[str] = None,
        explanation: Optional[str] = None,
    ) -> Dict[str, Any]:
        scope_enum = MemoryScope(scope.lower()) if scope.lower() in [s.value for s in MemoryScope] else MemoryScope.GLOBAL
        item = self.memory.set_preference(
            key=key,
            value=value,
            scope=scope_enum,
            scope_id=scope_id,
            explanation=explanation,
        )
        return {"status": "saved", "item": item.to_dict()}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "saved"}


class MemorySearchArgs(BaseModel):
    query: str = Field(description="Text or keyword to search in memories")
    category: Optional[str] = Field(default=None, description="Optional category filter (e.g. user_preference, task, project)")
    scope: Optional[str] = Field(default=None, description="Optional scope filter (global, project, device, session)")
    limit: int = Field(default=10, description="Max results to return")


class MemorySearchTool(BaseTool):
    name = "memory.search"
    description = "Searches stored memories, past task episodes, and preferences by keyword."
    permission_level = RiskLevel.SAFE
    args_schema = MemorySearchArgs
    timeout = 10.0

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        super().__init__()
        self.memory = memory_manager or MemoryManager()

    async def run(
        self,
        query: str,
        category: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        cat_enum = MemoryCategory(category) if category and category in [c.value for c in MemoryCategory] else None
        scope_enum = MemoryScope(scope) if scope and scope in [s.value for s in MemoryScope] else None
        results = self.memory.search(query=query, category=cat_enum, scope=scope_enum, limit=limit)
        return {
            "query": query,
            "count": len(results),
            "results": [r.to_dict() for r in results],
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": isinstance(result_data.get("results"), list)}


class MemoryForgetArgs(BaseModel):
    key: Optional[str] = Field(default=None, description="Key of the memory to forget")
    memory_id: Optional[str] = Field(default=None, description="Direct ID of the memory item")
    category: Optional[str] = Field(default=None, description="Optional category filter")
    scope: Optional[str] = Field(default=None, description="Optional scope filter")


class MemoryForgetTool(BaseTool):
    name = "memory.forget"
    description = "Removes or forgets a memory item or preference by key or ID."
    permission_level = RiskLevel.SENSITIVE
    args_schema = MemoryForgetArgs
    timeout = 10.0

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        super().__init__()
        self.memory = memory_manager or MemoryManager()

    async def run(
        self,
        key: Optional[str] = None,
        memory_id: Optional[str] = None,
        category: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> Dict[str, Any]:
        cat_enum = MemoryCategory(category) if category and category in [c.value for c in MemoryCategory] else None
        scope_enum = MemoryScope(scope) if scope and scope in [s.value for s in MemoryScope] else None
        success = self.memory.forget(
            memory_id=memory_id,
            key=key,
            category=cat_enum,
            scope=scope_enum,
        )
        return {"forgotten": success, "target": memory_id or key}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("forgotten"))}


class MemoryExplainArgs(BaseModel):
    key_or_id: str = Field(description="Memory key or UUID to explain provenance")


class MemoryExplainTool(BaseTool):
    name = "memory.explain"
    description = "Explains why and when a memory was saved, its source, and confidence score."
    permission_level = RiskLevel.SAFE
    args_schema = MemoryExplainArgs
    timeout = 10.0

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        super().__init__()
        self.memory = memory_manager or MemoryManager()

    async def run(self, key_or_id: str) -> Dict[str, Any]:
        info = self.memory.explain(key_or_id)
        if not info:
            return {"found": False, "explanation": f"No memory record found for '{key_or_id}'"}
        return {"found": True, "details": info}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True}
