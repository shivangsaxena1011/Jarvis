"""Phase 18: Cross-Device Continuity, Device Orchestration & Ambient Intelligence.

Exposes DeviceOrchestrator, TrustStore, PairingEngine, CapabilityEngine,
RoutingEngine, HandoffEngine, TransferEngine, AmbientEngine, and all core models.
"""

from core.devices.models import (
    AmbientContextState,
    ConnectionState,
    CrossDeviceCommand,
    Device,
    DeviceCapability,
    DevicePermission,
    DevicePlatform,
    DeviceTrustState,
    FileTransferSession,
    HandoffStatus,
    HandoffType,
    PairingSession,
    TaskHandoff,
    TransferStatus,
)
from core.devices.trust_store import TrustStore
from core.devices.pairing_engine import PairingEngine
from core.devices.capability_engine import CapabilityEngine
from core.devices.routing_engine import RoutingEngine, RoutingDecision
from core.devices.handoff_engine import HandoffEngine
from core.devices.transfer_engine import TransferEngine
from core.devices.ambient_engine import AmbientEngine
from core.devices.orchestrator import DeviceOrchestrator
from core.devices.mock_network import MockNetworkEnvironment

__all__ = [
    "AmbientContextState",
    "ConnectionState",
    "CrossDeviceCommand",
    "Device",
    "DeviceCapability",
    "DevicePermission",
    "DevicePlatform",
    "DeviceTrustState",
    "FileTransferSession",
    "HandoffStatus",
    "HandoffType",
    "PairingSession",
    "TaskHandoff",
    "TransferStatus",
    "TrustStore",
    "PairingEngine",
    "CapabilityEngine",
    "RoutingEngine",
    "RoutingDecision",
    "HandoffEngine",
    "TransferEngine",
    "AmbientEngine",
    "DeviceOrchestrator",
    "MockNetworkEnvironment",
]
