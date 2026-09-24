"""
SHIVANI Session Security
Manages session token generation, cryptographic verification, expiration,
and elevated privilege boundaries.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Dict, Optional
from pydantic import BaseModel, Field


class SessionToken(BaseModel):
    token: str
    user: str = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    is_elevated: bool = False


class SessionSecurityManager:
    def __init__(self, default_ttl_minutes: int = 120):
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self._sessions: Dict[str, SessionToken] = {}

    def create_session(self, user: str = "user", is_elevated: bool = False) -> str:
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        session = SessionToken(
            token=token,
            user=user,
            created_at=now,
            expires_at=now + self.default_ttl,
            is_elevated=is_elevated,
        )
        self._sessions[token] = session
        return token

    def validate_session(self, token: str) -> bool:
        session = self._sessions.get(token)
        if not session:
            return False
        if datetime.now(timezone.utc) > session.expires_at:
            del self._sessions[token]
            return False
        return True

    def is_elevated(self, token: str) -> bool:
        session = self._sessions.get(token)
        return bool(session and session.is_elevated and self.validate_session(token))

    def revoke_session(self, token: str) -> bool:
        if token in self._sessions:
            del self._sessions[token]
            return True
        return False
