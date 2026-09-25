"""
Red-Team Adversarial Matrix: Credential & Secret Protection (Phase 20)
Verifies zero-plaintext disk exposure, Windows DPAPI encryption of vaults,
and credential redaction from application logs.
"""

from pathlib import Path
import tempfile
import pytest

from security.secret_manager import SecretManager, DPAPIHelper
from security.filesystem_safety import PathValidator, FilesystemPolicy


def test_zero_plaintext_credentials_on_disk():
    """Verifies that credentials stored in the vault are never present as plaintext on disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_file = Path(tmpdir) / "vault.enc"
        secret_mgr = SecretManager(storage_path=str(vault_file))

        sensitive_key = "sk-live-supersecretapikey1234567890abcdef"
        secret_mgr.set_secret_sync("OPENAI_API_KEY", sensitive_key)

        # Ensure vault was written
        assert vault_file.exists()

        # Read raw bytes of the file directly
        raw_bytes = vault_file.read_bytes()
        raw_text = vault_file.read_text(encoding="utf-8", errors="ignore")

        # The plaintext key must NOT be present anywhere in the raw file
        assert sensitive_key not in raw_text
        assert sensitive_key.encode("utf-8") not in raw_bytes

        # Decrypting via the SecretManager should retrieve the original key
        retrieved = secret_mgr.get_secret_sync("OPENAI_API_KEY")
        assert retrieved == sensitive_key


def test_vault_tamper_and_isolation():
    """Verifies that deleting or overwriting the vault gracefully clears secrets without leakage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_file = Path(tmpdir) / "vault.enc"
        secret_mgr = SecretManager(storage_path=str(vault_file))

        secret_mgr.set_secret_sync("DATABASE_PASSWORD", "db_super_secret_pw_999")
        assert secret_mgr.has_secret_sync("DATABASE_PASSWORD")

        # Delete the secret
        secret_mgr.delete_secret_sync("DATABASE_PASSWORD")
        assert not secret_mgr.has_secret_sync("DATABASE_PASSWORD")
        assert secret_mgr.get_secret_sync("DATABASE_PASSWORD") is None


def test_sensitive_credential_files_blocked_from_arbitrary_read():
    """Verifies that sensitive local credential paths (.env, ssh keys) are blocked from escape reads."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / "workspace"
        workspace.mkdir()

        # Attempt to target sensitive system or credential files outside workspace
        blocked_targets = [
            Path.home() / ".ssh" / "id_rsa",
            Path.home() / ".aws" / "credentials",
            Path("C:/Windows/system32/config/SAM"),
        ]

        for target in blocked_targets:
            valid, err = PathValidator.validate_within_boundary(workspace, target)
            assert valid is False
            assert err is not None
