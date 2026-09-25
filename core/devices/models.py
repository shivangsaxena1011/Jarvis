"""Data models and enums for Phase 18: Cross-Device Continuity & Ambient Intelligence.

Covers device trust state machine, capabilities, permissions, connection states,
task handoffs, authenticated chunked file transfer, and ambient context boundaries.
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DeviceTrustState(str, enum.Enum):
    """Lifecycle state machine for device trust."""
    DISCOVERED = "discovered"
    PAIRING = "pairing"
    PENDING_APPROVAL = "pending_approval"
    TRUSTED = "trusted"
    BLOCKED = "blocked"
    REVOKED = "revoked"
    OFFLINE = "offline"


class DeviceCapability(str, enum.Enum):
    """Device hardware and software capability descriptors."""
    COMPUTER_CONTROL = "computer_control"
    BROWSER = "browser"
    FILES = "files"
    TERMINAL = "terminal"
    NOTIFICATIONS = "notifications"
    SCREENSHOT = "screenshot"
    UI_AUTOMATION = "ui_automation"
    CAMERA = "camera"
    VOICE = "voice"
    CLIPBOARD = "clipboard"
    LOCATION = "location"
    TOUCH = "touch"
    PHONE_CALLS = "phone_calls"
    SMS = "sms"


class DevicePermission(str, enum.Enum):
    """Granular per-device authorization tiers."""
    VIEW = "view"              # Can view status, notifications, read-only summaries
    COMMAND = "command"        # Can request predefined tools/actions within scope
    CONTROL = "control"        # Full automation/computer use or phone UI control
    TRANSFER = "transfer"      # Can exchange files and clipboard items
    ADMIN = "admin"            # Can manage pairing, trust, and emergency controls


class ConnectionState(str, enum.Enum):
    """Reachability and network transport status."""
    LOCAL = "local"            # Direct on-device loopback or USB
    LAN = "lan"                # Local Wi-Fi / subnet mesh
    REMOTE = "remote"          # Relayed via secure encrypted cloud/tailscale
    OFFLINE = "offline"        # Unreachable


class DevicePlatform(str, enum.Enum):
    """Target hardware and OS platform."""
    WINDOWS = "windows"
    ANDROID = "android"
    TABLET = "tablet"
    LAPTOP = "laptop"
    LINUX = "linux"
    MACOS = "macos"


class HandoffType(str, enum.Enum):
    """Semantics of cross-device task progression."""
    CONTINUE = "continue"      # Seamlessly pick up task execution where left off
    TRANSFER = "transfer"      # Transfer ownership/focus of task to target device
    DELEGATE = "delegate"      # Target device completes subtask and reports back
    MIRROR = "mirror"          # Mirror active view/session to secondary screen
    VIEW = "view"              # View status/live progress without execution control
    NOTIFY = "notify"          # Push alert or result artifact to target device


class HandoffStatus(str, enum.Enum):
    """Execution status of a task handoff."""
    INITIATED = "initiated"
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TransferStatus(str, enum.Enum):
    """Status of chunked file transfer."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AmbientContextState(str, enum.Enum):
    """Privacy boundary for ambient awareness.
    
    Strict zero-surveillance guarantee: NO covert mic, camera, screen, clipboard,
    or location tracking is ever permitted regardless of ambient context mode.
    """
    OFF = "off"                # No ambient awareness; strictly explicit commands
    TASK_ONLY = "task_only"    # Awareness active only during an explicit running task
    PROJECT = "project"        # Project-level context loaded when working on that project
    SESSION = "session"        # Active user session context across devices
    GLOBAL = "global"          # Aggregated device presence status (idle/active only)


@dataclass
class Device:
    """Represents a connected or paired device node in Shivani's mesh."""
    device_id: str
    display_name: str
    platform: str = DevicePlatform.WINDOWS.value
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    trust_state: DeviceTrustState = DeviceTrustState.DISCOVERED
    connection_state: ConnectionState = ConnectionState.LAN
    permissions: List[str] = field(default_factory=lambda: [DevicePermission.VIEW.value])
    battery_level: Optional[int] = None
    is_charging: bool = False
    public_key: Optional[str] = None
    auth_token: Optional[str] = None
    ip_address: Optional[str] = None
    port: int = 8765
    last_seen: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_online(self, timeout_sec: float = 60.0) -> bool:
        if self.connection_state == ConnectionState.OFFLINE:
            return False
        return (time.time() - self.last_seen) <= timeout_sec

    def has_capability(self, capability: str | DeviceCapability) -> bool:
        cap_val = capability.value if isinstance(capability, DeviceCapability) else capability
        return cap_val in self.capabilities

    def has_permission(self, permission: str | DevicePermission) -> bool:
        perm_val = permission.value if isinstance(permission, DevicePermission) else permission
        return perm_val in self.permissions or DevicePermission.ADMIN.value in self.permissions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "display_name": self.display_name,
            "platform": self.platform,
            "version": self.version,
            "capabilities": self.capabilities,
            "trust_state": self.trust_state.value if isinstance(self.trust_state, DeviceTrustState) else self.trust_state,
            "connection_state": self.connection_state.value if isinstance(self.connection_state, ConnectionState) else self.connection_state,
            "permissions": self.permissions,
            "battery_level": self.battery_level,
            "is_charging": self.is_charging,
            "public_key": self.public_key,
            "auth_token": self.auth_token,
            "ip_address": self.ip_address,
            "port": self.port,
            "last_seen": self.last_seen,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Device:
        trust_state = data.get("trust_state", DeviceTrustState.DISCOVERED)
        if isinstance(trust_state, str):
            try:
                trust_state = DeviceTrustState(trust_state)
            except ValueError:
                trust_state = DeviceTrustState.DISCOVERED

        conn_state = data.get("connection_state", ConnectionState.LAN)
        if isinstance(conn_state, str):
            try:
                conn_state = ConnectionState(conn_state)
            except ValueError:
                conn_state = ConnectionState.LAN

        return cls(
            device_id=data["device_id"],
            display_name=data.get("display_name", data["device_id"]),
            platform=data.get("platform", DevicePlatform.WINDOWS.value),
            version=data.get("version", "1.0.0"),
            capabilities=list(data.get("capabilities", [])),
            trust_state=trust_state,
            connection_state=conn_state,
            permissions=list(data.get("permissions", [DevicePermission.VIEW.value])),
            battery_level=data.get("battery_level"),
            is_charging=data.get("is_charging", False),
            public_key=data.get("public_key"),
            auth_token=data.get("auth_token"),
            ip_address=data.get("ip_address"),
            port=data.get("port", 8765),
            last_seen=data.get("last_seen", time.time()),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class PairingSession:
    """Ephemeral session for secure out-of-band mutual verification."""
    session_id: str
    device_id: str
    display_name: str
    platform: str
    code: str  # 6-digit cryptographic confirmation code / Short Authentication String (SAS)
    public_key: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 300)  # 5 min
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "display_name": self.display_name,
            "platform": self.platform,
            "code": self.code,
            "public_key": self.public_key,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "verified": self.verified,
            "metadata": self.metadata,
        }


@dataclass
class TaskHandoff:
    """Minimal, privacy-conscious execution context packet transferred between devices."""
    handoff_id: str
    task_id: str
    title: str
    source_device_id: str
    target_device_id: str
    handoff_type: HandoffType = HandoffType.CONTINUE
    context_payload: Dict[str, Any] = field(default_factory=dict)
    status: HandoffStatus = HandoffStatus.INITIATED
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 600)  # 10 min
    result_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "task_id": self.task_id,
            "title": self.title,
            "source_device_id": self.source_device_id,
            "target_device_id": self.target_device_id,
            "handoff_type": self.handoff_type.value if isinstance(self.handoff_type, HandoffType) else self.handoff_type,
            "context_payload": self.context_payload,
            "status": self.status.value if isinstance(self.status, HandoffStatus) else self.status,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "result_payload": self.result_payload,
            "error_message": self.error_message,
        }


@dataclass
class FileTransferSession:
    """Chunked, resumable file transfer session with SHA-256 integrity verification."""
    session_id: str
    filename: str
    source_device_id: str
    target_device_id: str
    file_size: int
    bytes_transferred: int = 0
    chunk_size: int = 64 * 1024  # 64 KB
    total_chunks: int = 0
    chunks_received: List[int] = field(default_factory=list)
    sha256_checksum: str = ""
    status: TransferStatus = TransferStatus.INITIATED
    local_path: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    error_message: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        if self.file_size <= 0:
            return 100.0 if self.status == TransferStatus.COMPLETED else 0.0
        return min(100.0, round((self.bytes_transferred / self.file_size) * 100.0, 2))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "filename": self.filename,
            "source_device_id": self.source_device_id,
            "target_device_id": self.target_device_id,
            "file_size": self.file_size,
            "bytes_transferred": self.bytes_transferred,
            "progress_percentage": self.progress_percentage,
            "chunk_size": self.chunk_size,
            "total_chunks": self.total_chunks,
            "chunks_received": len(self.chunks_received),
            "sha256_checksum": self.sha256_checksum,
            "status": self.status.value if isinstance(self.status, TransferStatus) else self.status,
            "local_path": self.local_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message,
        }


@dataclass
class CrossDeviceCommand:
    """Authenticated remote command with anti-replay nonce and timestamp."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_device_id: str = ""
    target_device_id: str = ""
    action: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    nonce: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)
    auth_token: Optional[str] = None
    signature: Optional[str] = None
    authorization_scope: str = DevicePermission.COMMAND.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "source_device_id": self.source_device_id,
            "target_device_id": self.target_device_id,
            "action": self.action,
            "parameters": self.parameters,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "auth_token": self.auth_token,
            "signature": self.signature,
            "authorization_scope": self.authorization_scope,
        }
