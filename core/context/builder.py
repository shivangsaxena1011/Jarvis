"""
SHIVANI Context Builder
Synthesizes multi-source context according to strict hierarchy:
1. Current User Request
2. Active Task / Goal / Checkpoints
3. Foreground App & Screen State
4. Relevant Scoped Memories & Explicit Preferences
5. Active Project Context
6. Recent Conversation / Execution History
"""

from typing import Any, Dict, List, Optional
from memory.manager import MemoryManager
from memory.models import MemoryCategory, MemoryItem, MemoryScope
from core.context.conversational import ConversationalContext, get_conversational_context
from tools.desktop.os import OperatingSystemAdapter, get_os_adapter


class ContextBuilder:
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        os_adapter: Optional[OperatingSystemAdapter] = None,
        conv_context: Optional[ConversationalContext] = None,
    ):
        self.memory = memory_manager
        self.os_adapter = os_adapter or get_os_adapter()
        self.conv_context = conv_context or get_conversational_context()

    def get_relevant_memories(
        self,
        query: str,
        project_id: Optional[str] = None,
        device_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[MemoryItem]:
        """Retrieves top relevant memories and preferences matching query without dumping entire memory."""
        if not self.memory:
            return []

        results: List[MemoryItem] = []
        seen_keys = set()

        # 1. Check for explicit keyword preferences (e.g. browser, editor, language, theme)
        query_lower = query.lower()
        key_mappings = {
            "browser": "preferred_browser",
            "chrome": "preferred_browser",
            "brave": "preferred_browser",
            "firefox": "preferred_browser",
            "edge": "preferred_browser",
            "editor": "preferred_editor",
            "vscode": "preferred_editor",
            "theme": "preferred_theme",
            "test": "preferred_test_runner",
            "phone": "preferred_device",
        }
        for kw, pref_key in key_mappings.items():
            if kw in query_lower and pref_key not in seen_keys:
                pref_val = self.memory.get_preference(pref_key, project_id=project_id, device_id=device_id)
                if pref_val is not None:
                    item = self.memory.store.get_by_key(
                        category=MemoryCategory.USER_PREFERENCE,
                        key=pref_key,
                    )
                    if item:
                        results.append(item)
                        seen_keys.add(pref_key)

        # 2. General search across memories
        search_hits = self.memory.search(query=query, limit=limit)
        for hit in search_hits:
            if hit.key not in seen_keys:
                results.append(hit)
                seen_keys.add(hit.key)

        return results[:limit]

    def build_prompt_context(
        self,
        query: str,
        task_id: Optional[str] = None,
        task_plan: Optional[Any] = None,
        project_id: Optional[str] = None,
        device_id: Optional[str] = None,
        max_chars: int = 4000,
    ) -> str:
        """Assembles structured prompt context respecting max character budget."""
        sections: List[str] = []

        # 1. Current User Request
        sections.append(f"### CURRENT USER REQUEST\n{query.strip()}")

        # 2. Active Task / Checkpoint
        if task_id and self.memory:
            chk = self.memory.task_memory.get_checkpoint(task_id)
            if chk:
                sections.append(
                    f"### ACTIVE TASK CHECKPOINT\n"
                    f"Task ID: {chk.get('task_id')}\n"
                    f"Stage: {chk.get('stage')}\n"
                    f"Step: {chk.get('step_index')}\n"
                    f"State: {chk.get('state')}"
                )
            elif task_plan:
                sections.append(f"### ACTIVE TASK PLAN\nPlan steps: {len(getattr(task_plan, 'steps', []))}")

        # 3. Foreground App & Visible Screen Context
        try:
            active_win = self.os_adapter.get_active_window()
            if active_win:
                sections.append(
                    f"### ACTIVE FOREGROUND WINDOW\n"
                    f"Title: {active_win.get('title', 'Unknown')}\n"
                    f"Process: {active_win.get('process_name', 'Unknown')}"
                )
        except Exception:
            pass

        # 4. Relevant Scoped Memories & Preferences
        relevant_memories = self.get_relevant_memories(
            query=query,
            project_id=project_id,
            device_id=device_id,
            limit=4,
        )
        if relevant_memories:
            mem_lines = []
            for m in relevant_memories:
                mem_lines.append(f"- [{m.category.value}] {m.key}: {m.value} (source: {m.source.value}, confidence: {m.confidence})")
            sections.append("### RELEVANT MEMORIES & PREFERENCES\n" + "\n".join(mem_lines))

        # 5. Project Context (if project_id provided)
        if project_id and self.memory:
            proj_facts = self.memory.semantic.list_project_facts(project_id)
            if proj_facts:
                pf_lines = [f"- {pf.key}: {pf.value}" for pf in proj_facts[:5]]
                sections.append(f"### PROJECT CONTEXT ({project_id})\n" + "\n".join(pf_lines))

        # 6. Recent Conversation History
        if self.conv_context:
            turns = self.conv_context.turns[-4:]
            if turns:
                history_lines = [f"{t.role.upper()}: {t.text}" for t in turns]
                sections.append("### RECENT CONVERSATION HISTORY\n" + "\n".join(history_lines))

        full_context = "\n\n".join(sections)
        if len(full_context) > max_chars:
            full_context = full_context[:max_chars] + "\n...[Context truncated for brevity]"

        return full_context
