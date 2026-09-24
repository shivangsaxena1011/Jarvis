"""
SHIVANI Base Connector Interface
Defines the standard contract for app and service connectors (GitHub, Slack, Notion, etc.).
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional

from connectors.models import AccountCredentials, AccountMetadata, AuthType, ConnectorStatus


class BaseConnector(ABC):
    """Abstract base connector for cloud and local third-party services."""

    name: str = "base_connector"
    provider: str = "generic"
    supported_auth_types: List[AuthType] = [AuthType.API_KEY]

    def __init__(self):
        self.status: ConnectorStatus = ConnectorStatus.DISCONNECTED
        self.active_account: Optional[AccountMetadata] = None
        self._credentials: Optional[AccountCredentials] = None
        self.logger = logging.getLogger(f"shivani.connectors.{self.provider}")

    @abstractmethod
    async def connect(
        self,
        account: AccountMetadata,
        credentials: Optional[AccountCredentials] = None,
    ) -> bool:
        """Establishes connection and authenticates with service."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Gracefully disconnects and resets session state."""
        pass

    @abstractmethod
    async def health(self) -> ConnectorStatus:
        """Performs ping or lightweight check to verify service connectivity."""
        pass

    @abstractmethod
    async def check_rate_limit(self) -> Dict[str, Any]:
        """Returns rate limit status: remaining calls, reset timestamp."""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Returns summary status for dashboard / telemetry."""
        return {
            "name": self.name,
            "provider": self.provider,
            "status": self.status.value,
            "account": self.active_account.account_name if self.active_account else None,
            "account_id": self.active_account.account_id if self.active_account else None,
            "rate_limit_remaining": (
                self.active_account.rate_limit_remaining if self.active_account else None
            ),
        }
