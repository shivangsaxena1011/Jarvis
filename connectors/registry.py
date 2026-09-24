"""
SHIVANI Connector Registry
Tracks available third-party service connectors, their operational statuses,
and coordinates with AccountManager for active credential injection.
"""

import logging
from typing import Any, Dict, List, Optional

from connectors.accounts import AccountManager
from connectors.base import BaseConnector
from connectors.models import ConnectorStatus

logger = logging.getLogger("shivani.connectors.registry")


class ConnectorRegistry:
    """Central registry of app and service connectors."""

    def __init__(self, account_manager: Optional[AccountManager] = None):
        self._connectors: Dict[str, BaseConnector] = {}
        self.account_manager = account_manager or AccountManager()

    def register_connector(self, connector: BaseConnector) -> None:
        """Registers a service connector and attempts auto-connection if an active account exists."""
        self._connectors[connector.provider] = connector
        logger.info(f"Registered connector for provider '{connector.provider}' ({connector.name})")

        # Auto-connect if active account configured
        active_account = self.account_manager.get_active_account(connector.provider)
        if active_account:
            creds = self.account_manager.get_credentials(active_account.account_id)
            connector.active_account = active_account
            connector._credentials = creds
            logger.info(f"Attached active account '{active_account.account_name}' to {connector.provider}")

    def unregister_connector(self, provider: str) -> bool:
        """Removes a connector from the registry."""
        if provider in self._connectors:
            del self._connectors[provider]
            logger.info(f"Unregistered connector for provider '{provider}'")
            return True
        return False

    def get_connector(self, provider: str) -> Optional[BaseConnector]:
        return self._connectors.get(provider)

    def list_connectors(self) -> List[Dict[str, Any]]:
        return [c.get_status() for c in self._connectors.values()]

    async def check_all_health(self) -> Dict[str, ConnectorStatus]:
        """Runs health checks on all registered connectors."""
        results: Dict[str, ConnectorStatus] = {}
        for provider, conn in self._connectors.items():
            try:
                results[provider] = await conn.health()
            except Exception as e:
                logger.error(f"Health check failed for connector '{provider}': {e}")
                results[provider] = ConnectorStatus.ERROR
        return results
