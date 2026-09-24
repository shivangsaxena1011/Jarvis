"""
SHIVANI Security Subsystem Package
Provides unified 5-tier permissions, dynamic policy evaluation, DPAPI secret management,
prompt injection defense, command sandboxing, filesystem safety, and structured audit logging.
"""

from security.permissions import (
    RiskLevel,
    Permission,
    PolicyMode,
    ApprovalStatus,
    ApprovalRequest,
)
from security.policy_engine import PolicyEngine
from security.risk_classifier import RiskClassifier
from security.secret_manager import SecretManager, get_secret_manager, DPAPIHelper
from security.secure_storage import SecureStorage
from security.session_security import SessionSecurityManager, SessionToken
from security.device_security import DeviceSecurityManager
from security.prompt_injection import PromptInjectionClassifier, ContentCategory
from security.command_validation import CommandPolicy, CommandValidator, CommandRiskClassifier, CommandStatus
from security.filesystem_safety import FilesystemPolicy, PathValidator, FileOperationGuard
from security.audit_logger import StructuredAuditLogger, AuditLogger
from security.sandbox import ProcessSandbox
from security.security_events import SecurityEventType, SecurityEventDispatcher

# Backward compatibility alias
PermissionEngine = PolicyEngine

__all__ = [
    "RiskLevel",
    "Permission",
    "PolicyMode",
    "ApprovalStatus",
    "ApprovalRequest",
    "PolicyEngine",
    "PermissionEngine",
    "RiskClassifier",
    "SecretManager",
    "get_secret_manager",
    "DPAPIHelper",
    "SecureStorage",
    "SessionSecurityManager",
    "SessionToken",
    "DeviceSecurityManager",
    "PromptInjectionClassifier",
    "ContentCategory",
    "CommandPolicy",
    "CommandValidator",
    "CommandRiskClassifier",
    "CommandStatus",
    "FilesystemPolicy",
    "PathValidator",
    "FileOperationGuard",
    "StructuredAuditLogger",
    "AuditLogger",
    "ProcessSandbox",
    "SecurityEventType",
    "SecurityEventDispatcher",
]
