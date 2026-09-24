"""
Tests for Connectors: status, BaseConnector, OAuth PKCE flow, and ConnectorRegistry.
"""

import pytest
from connectors.base import BaseConnector
from connectors.models import AccountCredentials, AccountMetadata, AuthType, ConnectorStatus
from connectors.oauth import OAuthFlowManager
from connectors.registry import ConnectorRegistry


class MockCloudConnector(BaseConnector):
    name = "mock_cloud"
    provider = "mock_service"
    supported_auth_types = [AuthType.API_KEY]

    async def connect(self, account: AccountMetadata, credentials: AccountCredentials = None) -> bool:
        self.active_account = account
        self.status = ConnectorStatus.CONNECTED
        return True

    async def disconnect(self) -> bool:
        self.active_account = None
        self.status = ConnectorStatus.DISCONNECTED
        return True

    async def health(self) -> ConnectorStatus:
        return self.status

    async def check_rate_limit(self):
        return {"remaining": 5000, "reset": 1234567890}


@pytest.mark.asyncio
async def test_connector_lifecycle():
    conn = MockCloudConnector()
    assert conn.status == ConnectorStatus.DISCONNECTED

    meta = AccountMetadata(
        account_id="acc_001",
        account_name="Test Account",
        provider="mock_service",
    )
    ok = await conn.connect(meta)
    assert ok is True
    assert conn.status == ConnectorStatus.CONNECTED
    assert conn.get_status()["account_id"] == "acc_001"

    disc = await conn.disconnect()
    assert disc is True
    assert conn.status == ConnectorStatus.DISCONNECTED


def test_oauth_pkce_flow():
    oauth = OAuthFlowManager()

    # Generate authorization request
    auth_url, state = oauth.generate_authorization_request(
        provider="github",
        auth_endpoint="https://github.com/login/oauth/authorize",
        client_id="client_123",
        redirect_uri="http://localhost:8000/callback",
        scopes=["repo", "user"],
    )

    assert "client_123" in auth_url
    assert "code_challenge=" in auth_url
    assert state in auth_url

    # Validate state callback
    validated = oauth.validate_callback_state(state)
    assert validated is not None
    assert validated.provider == "github"

    # Second validation fails (single-use token protection)
    replay = oauth.validate_callback_state(state)
    assert replay is None
