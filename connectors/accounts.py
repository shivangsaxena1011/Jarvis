"""
SHIVANI Multi-Account Manager
Securely persists and manages multiple accounts per connector (e.g. GitHub personal vs work).
Ensures zero credential leakage to logs or agent contexts via DPAPI-backed SecureStorage.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from core.config.app_dirs import AppDirectories, get_app_dirs
from security.secure_storage import SecureStorage
from connectors.models import AccountCredentials, AccountMetadata

logger = logging.getLogger("shivani.connectors.accounts")


class AccountManager:
    """Manages multi-account credentials and active context selection."""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = get_app_dirs().config_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.storage_dir / "accounts_meta.json"
        self.credentials_file = self.storage_dir / "accounts_creds.enc"

        self._accounts: Dict[str, AccountMetadata] = {}
        self._credentials: Dict[str, AccountCredentials] = {}
        self._load()

    def _load(self) -> None:
        """Loads account metadata and encrypted credentials."""
        # 1. Load metadata (non-sensitive)
        if self.metadata_file.exists():
            try:
                import json
                data = json.loads(self.metadata_file.read_text(encoding="utf-8"))
                for acc_id, m in data.items():
                    self._accounts[acc_id] = AccountMetadata(**m)
            except Exception as e:
                logger.warning(f"Failed to load accounts metadata: {e}")

        # 2. Load encrypted credentials
        if self.credentials_file.exists():
            try:
                creds_data = SecureStorage.load_encrypted_json(self.credentials_file)
                if creds_data:
                    for acc_id, c in creds_data.items():
                        self._credentials[acc_id] = AccountCredentials(**c)
            except Exception as e:
                logger.warning(f"Failed to load encrypted credentials: {e}")

    def _save(self) -> None:
        """Persists metadata to json and credentials to encrypted store."""
        try:
            import json
            meta_dict = {k: v.model_dump(mode="json") for k, v in self._accounts.items()}
            self.metadata_file.write_text(json.dumps(meta_dict, indent=2), encoding="utf-8")

            creds_dict = {k: v.model_dump(mode="json") for k, v in self._credentials.items()}
            SecureStorage.save_encrypted_json(self.credentials_file, creds_dict)
        except Exception as e:
            logger.error(f"Failed to save account records: {e}")

    def save_account(
        self,
        metadata: AccountMetadata,
        credentials: Optional[AccountCredentials] = None,
    ) -> bool:
        """Adds or updates an account."""
        # If this is the first account for provider or marked active, ensure only one active
        if metadata.is_active:
            for acc in self._accounts.values():
                if acc.provider == metadata.provider and acc.account_id != metadata.account_id:
                    acc.is_active = False

        self._accounts[metadata.account_id] = metadata
        if credentials:
            self._credentials[metadata.account_id] = credentials

        self._save()
        logger.info(f"Saved account '{metadata.account_name}' ({metadata.account_id}) for {metadata.provider}")
        return True

    def get_account(self, account_id: str) -> Optional[AccountMetadata]:
        return self._accounts.get(account_id)

    def get_credentials(self, account_id: str) -> Optional[AccountCredentials]:
        """Retrieves raw decrypted credentials for authorized internal connector execution."""
        return self._credentials.get(account_id)

    def list_accounts(self, provider: Optional[str] = None) -> List[AccountMetadata]:
        """Lists accounts, optionally filtered by provider. Strips sensitive tokens."""
        res: List[AccountMetadata] = []
        for acc in self._accounts.values():
            if provider is None or acc.provider == provider:
                res.append(acc)
        return res

    def get_active_account(self, provider: str) -> Optional[AccountMetadata]:
        """Retrieves currently active account for provider."""
        for acc in self._accounts.values():
            if acc.provider == provider and acc.is_active:
                return acc
        # Fallback to any account for that provider if none marked active
        for acc in self._accounts.values():
            if acc.provider == provider:
                return acc
        return None

    def switch_active_account(self, provider: str, account_id: str) -> bool:
        """Sets the specified account as active for a given provider."""
        target = self.get_account(account_id)
        if not target or target.provider != provider:
            return False

        for acc in self._accounts.values():
            if acc.provider == provider:
                acc.is_active = (acc.account_id == account_id)

        self._save()
        logger.info(f"Switched active {provider} account to '{target.account_name}' ({account_id})")
        return True

    def remove_account(self, account_id: str) -> bool:
        """Deletes account metadata and encrypted credentials."""
        removed = False
        if account_id in self._accounts:
            del self._accounts[account_id]
            removed = True
        if account_id in self._credentials:
            del self._credentials[account_id]
            removed = True
        if removed:
            self._save()
            logger.info(f"Removed account {account_id}")
        return removed
