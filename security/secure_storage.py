"""
SHIVANI Secure Storage
Encrypts and decrypts structured JSON files and binary payloads on disk
using DPAPI encryption to protect cache, tokens, and sensitive task data.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import json
from security.secret_manager import DPAPIHelper


class SecureStorage:
    @classmethod
    def save_encrypted_json(cls, filepath: Path, data: Dict[str, Any]) -> bool:
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            raw_bytes = json.dumps(data).encode("utf-8")
            encrypted = DPAPIHelper.protect(raw_bytes)
            with open(filepath, "wb") as f:
                f.write(encrypted)
            return True
        except Exception:
            return False

    @classmethod
    def load_encrypted_json(cls, filepath: Path) -> Optional[Dict[str, Any]]:
        if not filepath.exists():
            return None
        try:
            with open(filepath, "rb") as f:
                encrypted = f.read()
            decrypted = DPAPIHelper.unprotect(encrypted)
            return json.loads(decrypted.decode("utf-8"))
        except Exception:
            return None

    @classmethod
    def save_encrypted_bytes(cls, filepath: Path, data: bytes) -> bool:
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            encrypted = DPAPIHelper.protect(data)
            with open(filepath, "wb") as f:
                f.write(encrypted)
            return True
        except Exception:
            return False

    @classmethod
    def load_encrypted_bytes(cls, filepath: Path) -> Optional[bytes]:
        if not filepath.exists():
            return None
        try:
            with open(filepath, "rb") as f:
                encrypted = f.read()
            return DPAPIHelper.unprotect(encrypted)
        except Exception:
            return None
