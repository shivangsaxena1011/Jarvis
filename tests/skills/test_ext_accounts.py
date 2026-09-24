"""
Tests for AccountManager: multi-account storage, context switching, and credential isolation.
"""

from pathlib import Path
import pytest
from connectors.accounts import AccountManager
from connectors.models import AccountCredentials, AccountMetadata, AuthType


def test_multi_account_management(tmp_path: Path):
    mgr = AccountManager(storage_dir=tmp_path)

    # Add Personal GitHub
    personal_meta = AccountMetadata(
        account_id="gh_personal",
        account_name="Personal GitHub",
        provider="github",
        auth_type=AuthType.API_KEY,
        is_active=True,
    )
    personal_creds = AccountCredentials(
        account_id="gh_personal",
        provider="github",
        api_key="ghp_personal_secret_token",
    )
    mgr.save_account(personal_meta, personal_creds)

    # Add Work GitHub
    work_meta = AccountMetadata(
        account_id="gh_work",
        account_name="Work GitHub",
        provider="github",
        auth_type=AuthType.API_KEY,
        is_active=False,
    )
    work_creds = AccountCredentials(
        account_id="gh_work",
        provider="github",
        api_key="ghp_work_secret_token",
    )
    mgr.save_account(work_meta, work_creds)

    # 1. List accounts
    accounts = mgr.list_accounts("github")
    assert len(accounts) == 2

    # 2. Check active account
    active = mgr.get_active_account("github")
    assert active is not None
    assert active.account_id == "gh_personal"

    # 3. Switch active account to work
    mgr.switch_active_account("github", "gh_work")
    active_switched = mgr.get_active_account("github")
    assert active_switched.account_id == "gh_work"

    # 4. Decrypt credentials for authorized use
    retrieved_creds = mgr.get_credentials("gh_work")
    assert retrieved_creds is not None
    assert retrieved_creds.api_key == "ghp_work_secret_token"
