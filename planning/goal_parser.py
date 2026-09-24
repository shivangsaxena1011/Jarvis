"""
SHIVANI Goal Parser & Clarification Engine.
Converts natural language queries into structured Goals and identifies missing critical parameters.
"""

from typing import Optional, Dict, Any, List
import re
from planning.models import Goal
from memory.manager import MemoryManager


class GoalParser:
    """Parses natural language requests into structured Goals with ambiguity detection."""

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory = memory_manager

    def parse(self, query: str) -> Goal:
        """Parses natural language into a structured Goal."""
        q_clean = query.strip()
        q_lower = q_clean.lower()

        # 1. Extract desired outputs
        desired_outputs: List[str] = []
        if any(w in q_lower for w in ["research", "investigate", "survey"]):
            desired_outputs.append("research_findings")
        if any(w in q_lower for w in ["report", "document", "readme", "doc"]):
            desired_outputs.append("report")
        if any(w in q_lower for w in ["presentation", "slides", "deck", "pitch"]):
            desired_outputs.append("presentation")
        if any(w in q_lower for w in ["linkedin", "post", "tweet", "social"]):
            desired_outputs.append("social_post")
        if any(w in q_lower for w in ["code", "build", "implement", "feature", "patch", "fix"]):
            desired_outputs.append("code")
        if any(w in q_lower for w in ["test", "verify", "benchmark"]):
            desired_outputs.append("test_results")

        if not desired_outputs:
            desired_outputs.append("direct_execution")

        # 2. Extract preferences from memory
        preferences: Dict[str, Any] = {}
        if self.memory:
            try:
                # Query common preference keys
                for key in ["default_browser", "coding_language", "report_format", "theme"]:
                    val = self.memory.preferences.get_preference(key)
                    if val:
                        preferences[key] = val
            except Exception:
                pass

        # 3. Check for approval requirements
        approval_requirements: List[str] = []
        if any(w in q_lower for w in ["send email", "bhejo email", "post on linkedin", "deploy", "delete file"]):
            approval_requirements.append("user_confirmation_before_publishing")

        # 4. Clarification check: Detect missing critical parameters
        needs_clarification, clar_q, clar_opts = self._check_clarification(q_clean, q_lower)

        return Goal(
            raw_query=q_clean,
            objective=q_clean,
            scope="composite" if len(desired_outputs) > 1 else "focused",
            desired_outputs=desired_outputs,
            constraints=[],
            preferences=preferences,
            approval_requirements=approval_requirements,
            needs_clarification=needs_clarification,
            clarification_question=clar_q,
            clarification_options=clar_opts,
        )

    def _check_clarification(self, query: str, query_lower: str) -> tuple[bool, Optional[str], List[str]]:
        """Identifies if critical missing parameters prevent safe autonomous execution."""
        # Email sending without recipient
        if re.search(r"\b(send|draft and send|bhejo)\b.*\b(email|mail)\b", query_lower):
            # Check if recipient email address or name exists (contains '@' or 'to <name>')
            has_recipient = "@" in query or bool(re.search(r"\b(to|recipient)\s+[a-zA-Z0-9_\-\.]+", query_lower))
            if not has_recipient:
                return (
                    True,
                    "Who should receive this email?",
                    ["User contacts", "Draft without sending", "Specify recipient email"],
                )

        # File transfer to mobile without source file
        if "transfer" in query_lower and ("phone" in query_lower or "mobile" in query_lower):
            has_file = bool(re.search(r"\b(file|photo|image|document|presentation|\.[a-zA-Z0-9]{2,4})\b", query_lower))
            if not has_file or query_lower.strip() in ["transfer to phone", "phone mein transfer karo"]:
                return (
                    True,
                    "Which file or document would you like to transfer to your phone?",
                    ["Latest generated report", "Latest presentation", "Browse local files"],
                )

        # Explicit ambiguous single-word commands
        if query_lower in ["delete it", "hata do", "remove", "clean"]:
            return (
                True,
                "What specific file or resource should be removed?",
                ["Cancel action", "Specify path"],
            )

        return (False, None, [])
