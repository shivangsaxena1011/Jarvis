"""
SHIVANI Data Management & Governance Package (Phase 20)
Provides backup/restore, export, verification, and privacy-compliant data deletion.
"""

from core.data.backup_manager import BackupManager
from core.data.data_manager import DataManager

__all__ = ["BackupManager", "DataManager"]
