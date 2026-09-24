"""
SHIVANI OAuth2 Flow Manager
Handles OAuth2 authorization URLs, PKCE challenges, state validation against CSRF,
and token refresh rotation.
"""

import base64
import hashlib
import os
import secrets
import time
from typing import Dict, Optional, Tuple
from pydantic import BaseModel, Field


class OAuthState(BaseModel):
    state: str
    provider: str
    code_verifier: str
    redirect_uri: str
    scopes: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class OAuthFlowManager:
    """Manages PKCE-enabled OAuth 2.0 authorization flows."""

    def __init__(self, state_ttl_seconds: float = 600.0):
        self.state_ttl = state_ttl_seconds
        self._pending_states: Dict[str, OAuthState] = {}

    def generate_authorization_request(
        self,
        provider: str,
        auth_endpoint: str,
        client_id: str,
        redirect_uri: str,
        scopes: list[str],
    ) -> Tuple[str, str]:
        """
        Creates PKCE verifier/challenge and returns (auth_url, state_token).
        """
        # Generate state & PKCE
        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(48)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest())
            .decode("utf-8")
            .rstrip("=")
        )

        oauth_state = OAuthState(
            state=state,
            provider=provider,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
            scopes=scopes,
        )
        self._pending_states[state] = oauth_state

        scope_str = "%20".join(scopes)
        auth_url = (
            f"{auth_endpoint}?response_type=code&client_id={client_id}"
            f"&redirect_uri={redirect_uri}&scope={scope_str}&state={state}"
            f"&code_challenge={code_challenge}&code_challenge_method=S256"
        )

        return auth_url, state

    def validate_callback_state(self, state: str) -> Optional[OAuthState]:
        """Validates state parameter, ensuring flow is not expired or replayed."""
        self._cleanup_expired()
        oauth_state = self._pending_states.pop(state, None)
        if not oauth_state:
            return None
        if time.time() - oauth_state.created_at > self.state_ttl:
            return None
        return oauth_state

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired = [s for s, data in self._pending_states.items() if now - data.created_at > self.state_ttl]
        for s in expired:
            del self._pending_states[s]
