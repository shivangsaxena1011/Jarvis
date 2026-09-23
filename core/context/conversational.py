"""
SHIVANI Conversational Context & Multi-Turn Controller
Retains conversational state across turns, resolves follow-up queries,
and handles low-confidence speech clarification prompts.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    role: str # "user" | "shivani"
    text: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    task_id: Optional[str] = None
    confidence: float = 1.0


class ConversationalContext(BaseModel):
    active_app: Optional[str] = None
    active_domain: Optional[str] = None # "browser", "youtube", "coding", "filesystem"
    last_subject: Optional[str] = None
    turns: List[ConversationTurn] = Field(default_factory=list)

    def record_turn(self, role: str, text: str, task_id: Optional[str] = None, confidence: float = 1.0) -> None:
        turn = ConversationTurn(role=role, text=text, task_id=task_id, confidence=confidence)
        self.turns.append(turn)
        if len(self.turns) > 20:
            self.turns.pop(0)

        # Update conversational state
        text_lower = text.lower()
        if "youtube" in text_lower:
            self.active_domain = "youtube"
            self.last_subject = "youtube"
            if "chrome" in text_lower:
                self.active_app = "chrome"
        elif "chrome" in text_lower:
            self.active_app = "chrome"
            self.active_domain = "browser"
        elif "notepad" in text_lower:
            self.active_app = "notepad"
            self.active_domain = "editor"


    def resolve_followup(self, query: str) -> str:
        """
        Resolves follow-up commands that omit context (e.g. 'Arijit Singh search karo').
        """
        clean = query.strip()
        clean_lower = clean.lower()

        # Follow-up search command in YouTube / media domain
        if self.active_domain == "youtube" or (self.last_subject and "youtube" in self.last_subject):
            if re.search(r"\b(?:search|play|dhoondo|chalao)\b", clean_lower):
                # If target website is not mentioned, bind to active YouTube context
                if "youtube" not in clean_lower and "google" not in clean_lower:
                    clean = f"In YouTube, {clean}"

        # Follow-up navigation in browser
        elif self.active_app == "chrome" and re.search(r"\b(?:youtube|github|linkedin|google)\b", clean_lower):
            if "chrome" not in clean_lower:
                clean = f"Open {clean} in Chrome"

        # Deictic resolution: 'isko band karo', 'ye close karo'
        if re.search(r"\b(?:isko|ye|ise|this)\s+(?:band|close)\b", clean_lower):
            if self.active_app:
                clean = f"close {self.active_app}"

        return clean

    def check_uncertainty_clarification(self, text: str, confidence: float, threshold: float = 0.65) -> Optional[str]:
        """
        Generates clarification question if speech recognition confidence is low,
        preventing false confirmations or accidental executions.
        """
        if confidence >= threshold or not text.strip():
            return None

        # Format clarification in Hindi / Hinglish
        clean = text.strip()
        return f"क्या आपने कहा कि '{clean}' करना है?"


# Global singleton
_global_conv_context = ConversationalContext()

def get_conversational_context() -> ConversationalContext:
    return _global_conv_context
