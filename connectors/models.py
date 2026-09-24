"""
SHIVANI App Connector Models
Data schemas for third-party service connectors, authentication types, and account credentials.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConnectorStatus(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    RATE_LIMITED = "RATE_LIMITED"


class AuthType(str, Enum):
    API_KEY = "API_KEY"
    OAUTH2 = "OAUTH2"
    SESSION_TOKEN = "SESSION_TOKEN"
    LOCAL_CLI = "LOCAL_CLI"
    NONE = "NONE"


class AccountMetadata(BaseModel):
    account_id: str = Field(..., description="Unique ID for the account (e.g. 'github_personal', 'github_work')")
    account_name: str = Field(..., description="Human-friendly label (e.g. 'Personal GitHub')")
    provider: str = Field(..., description="Connector provider identifier, e.g. 'github', 'gmail', 'slack'")
    auth_type: AuthType = Field(default=AuthType.API_KEY)
    is_active: bool = Field(default=True, description="Whether this account is currently active for operations")
    scopes: List[str] = Field(default_factory=list)
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AccountCredentials(BaseModel):
    account_id: str
    provider: str
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expiry: Optional[datetime] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    extra_headers: Dict[str, str] = Field(default_factory=dict)
