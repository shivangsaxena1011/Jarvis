"""Context Window Management, Token Budgets & History Compression for Phase 19.

Maintains strict token budgets, prioritizes actionable task execution states over bloated chit-chat,
and compresses long conversational trajectories into structured milestones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("shivani.ai.context")


@dataclass
class ConversationContext:
    """Encapsulates active conversation state, token budget, and milestones."""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    token_budget: int = 4096
    metadata: Dict[str, Any] = field(default_factory=dict)



class ContextManager:
    """Manages prompt budgets, compresses conversational history, and enforces token bounds."""

    def __init__(self, default_token_budget: int = 4096):
        self.default_token_budget = default_token_budget

    def estimate_tokens(self, text: str) -> int:
        """Heuristic token estimator (approximately 4 characters per token)."""
        return max(1, len(text) // 4)

    def compress_history(self, history: List[Dict[str, Any]], target_token_limit: int = 2048) -> List[Dict[str, Any]]:
        """Compress a long conversational/action history into compact milestones."""
        if not history:
            return []

        total_est = sum(self.estimate_tokens(str(item.get("content", ""))) for item in history)
        if total_est <= target_token_limit:
            return history

        # Preserve the initial system objective and the most recent 3 turns
        if len(history) <= 4:
            return history

        initial = history[0]
        recent = history[-3:]
        middle = history[1:-3]

        # Summarize middle actions
        summary_bullets = []
        for step in middle:
            role = step.get("role", "user")
            content = str(step.get("content", ""))[:80]
            summary_bullets.append(f"- [{role.upper()}]: {content}...")

        compact_summary = {
            "role": "system",
            "content": f"[Compressed History Milestone ({len(middle)} steps)]:\n" + "\n".join(summary_bullets[:5]),
        }

        compressed = [initial, compact_summary] + recent
        logger.info(f"Compressed history from {len(history)} items to {len(compressed)} items.")
        return compressed

    def format_task_prompt(
        self,
        objective: str,
        plan_steps: List[str],
        completed_steps: List[str],
        current_state: str,
        artifacts: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Build structured task prompt strictly adhering to token budgets."""
        budget = max_tokens or self.default_token_budget

        sections = [
            f"# OBJECTIVE: {objective}",
            f"# CURRENT STATE: {current_state}",
            f"# COMPLETED ({len(completed_steps)}): " + "; ".join(completed_steps[-3:]),
            f"# NEXT STEPS: " + "; ".join(plan_steps[:3]),
        ]
        if artifacts:
            sections.append(f"# ARTIFACTS: {', '.join(artifacts[:5])}")

        full_prompt = "\n".join(sections)
        # Ensure within budget
        if self.estimate_tokens(full_prompt) > budget:
            full_prompt = full_prompt[:budget * 4]

        return full_prompt
