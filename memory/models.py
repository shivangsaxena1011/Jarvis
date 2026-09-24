"""
SHIVANI Memory Models
Defines scopes, categories, confidence scoring, provenance tracking,
and secret redaction rules for long-term and short-term memory.
"""

from datetime import datetime, timezone
from enum import Enum
import json
import re
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, model_validator


class MemoryScope(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"
    TASK = "task"
    DEVICE = "device"
    SESSION = "session"


class MemoryCategory(str, Enum):
    USER_PREFERENCE = "user_preference"
    PROJECT = "project"
    WORKFLOW = "workflow"
    DEVICE = "device"
    TASK = "task"
    CONTEXT = "context"
    SYSTEM_SETTING = "system_setting"


class MemorySource(str, Enum):
    EXPLICIT_USER = "explicit_user"
    INFERRED = "inferred"
    TASK_RESULT = "task_result"
    SYSTEM = "system"


class SecretRedactor:
    """Detects and redacts passwords, tokens, API keys, and sensitive secrets."""

    SECRET_KEY_PATTERNS = [
        re.compile(r"(password|passwd|pwd|secret|api[_\-]?key|access[_\-]?token|auth[_\-]?token|bearer|private[_\-]?key)", re.IGNORECASE),
    ]

    SECRET_VALUE_PATTERNS = [
        re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"sk-[a-zA-Z0-9]{20,}"),
        re.compile(r"(?:api[_\-]?key|secret|token|password)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?", re.IGNORECASE),
    ]

    @classmethod
    def redact_text(cls, text: str) -> str:
        if not isinstance(text, str):
            return text
        redacted = text
        for pattern in cls.SECRET_VALUE_PATTERNS:
            redacted = pattern.sub("[REDACTED_SECRET]", redacted)
        return redacted

    @classmethod
    def redact_value(cls, key: str, val: Any) -> Any:
        if isinstance(val, str):
            # Check key name
            for kpat in cls.SECRET_KEY_PATTERNS:
                if kpat.search(key):
                    return "[REDACTED_SECRET]"
            return cls.redact_text(val)
        elif isinstance(val, dict):
            return cls.redact_dict(val)
        elif isinstance(val, list):
            return [cls.redact_value(key, item) for item in val]
        return val

    @classmethod
    def redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}
        for k, v in data.items():
            is_secret_key = any(kpat.search(k) for kpat in cls.SECRET_KEY_PATTERNS)
            if is_secret_key:
                cleaned[k] = "[REDACTED_SECRET]"
            else:
                cleaned[k] = cls.redact_value(k, v)
        return cleaned


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: MemoryCategory
    scope: MemoryScope = MemoryScope.GLOBAL
    scope_id: Optional[str] = None
    key: str
    value: Any
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: MemorySource = MemorySource.EXPLICIT_USER
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    explanation: Optional[str] = None

    @model_validator(mode="after")
    def sanitize_secrets(self) -> "MemoryItem":
        # Redact secrets in key, value, metadata, and explanation
        if isinstance(self.key, str):
            self.key = SecretRedactor.redact_text(self.key)
        self.value = SecretRedactor.redact_value(self.key, self.value)
        if self.metadata:
            self.metadata = SecretRedactor.redact_dict(self.metadata)
        if self.explanation:
            self.explanation = SecretRedactor.redact_text(self.explanation)
        return self

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if self.expires_at is None:
            return False
        current = now or utc_now()
        # Ensure comparison is timezone aware
        if self.expires_at.tzinfo is None:
            expires = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires = self.expires_at
        return current > expires

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "scope": self.scope.value,
            "scope_id": self.scope_id,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
            "explanation": self.explanation,
        }
