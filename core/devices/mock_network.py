"""Synthetic Multi-Device Network Environment for Phase 18 Testing.

Provides deterministic multi-device topologies, simulated link latency/disconnections,
corrupted chunk injection for integrity tests, and simulated cross-device task progression.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from core.devices.models import (
    ConnectionState,
    Device,
    DeviceCapability,
    DevicePermission,
    DevicePlatform,
    DeviceTrustState,
    FileTransferSession,
    HandoffStatus,
    HandoffType,
    TaskHandoff,
)
from core.devices.orchestrator import DeviceOrchestrator


class MockNetworkEnvironment:
    """Configures a simulated multi-device mesh network for robust deterministic testing."""

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="shivani_mesh_test_")
        self.db_path = os.path.join(self.temp_dir, "test_devices.db")
        self.orchestrator = DeviceOrchestrator(
            db_path=self.db_path,
            primary_device_id="pc-workstation-001",
        )
        self.setup_default_mesh()

    def setup_default_mesh(self) -> None:
        """Populate standard devices: Windows PC (primary), Android Phone, and Travel Laptop."""
        # Android companion device
        phone = Device(
            device_id="phone-galaxy-001",
            display_name="Shivani Galaxy S24",
            platform=DevicePlatform.ANDROID.value,
            capabilities=[
                DeviceCapability.UI_AUTOMATION.value,
                DeviceCapability.NOTIFICATIONS.value,
                DeviceCapability.CAMERA.value,
                DeviceCapability.PHONE_CALLS.value,
                DeviceCapability.FILES.value,
                DeviceCapability.CLIPBOARD.value,
                DeviceCapability.TOUCH.value,
            ],
            trust_state=DeviceTrustState.TRUSTED,
            connection_state=ConnectionState.LAN,
            permissions=[
                DevicePermission.VIEW.value,
                DevicePermission.COMMAND.value,
                DevicePermission.TRANSFER.value,
                DevicePermission.CONTROL.value,
            ],
            battery_level=88,
            is_charging=False,
            last_seen=time.time(),
        )
        self.orchestrator.trust_store.upsert_device(phone)

        # Secondary Windows laptop
        laptop = Device(
            device_id="laptop-travel-001",
            display_name="Shivani Surface Laptop",
            platform=DevicePlatform.WINDOWS.value,
            capabilities=[
                DeviceCapability.COMPUTER_CONTROL.value,
                DeviceCapability.BROWSER.value,
                DeviceCapability.FILES.value,
                DeviceCapability.TERMINAL.value,
                DeviceCapability.NOTIFICATIONS.value,
            ],
            trust_state=DeviceTrustState.TRUSTED,
            connection_state=ConnectionState.LAN,
            permissions=[
                DevicePermission.VIEW.value,
                DevicePermission.COMMAND.value,
                DevicePermission.TRANSFER.value,
            ],
            battery_level=95,
            is_charging=True,
            last_seen=time.time(),
        )
        self.orchestrator.trust_store.upsert_device(laptop)

    def simulate_disconnect(self, device_id: str) -> None:
        """Simulate a device going offline."""
        dev = self.orchestrator.trust_store.get_device(device_id)
        if dev:
            dev.connection_state = ConnectionState.OFFLINE
            dev.last_seen = time.time() - 3600.0  # 1 hour ago
            self.orchestrator.trust_store.upsert_device(dev)

    def simulate_reconnect(self, device_id: str) -> None:
        """Simulate a device coming back online."""
        dev = self.orchestrator.trust_store.get_device(device_id)
        if dev:
            dev.connection_state = ConnectionState.LAN
            dev.last_seen = time.time()
            self.orchestrator.trust_store.upsert_device(dev)

    def simulate_full_file_transfer(
        self,
        source_id: str,
        target_id: str,
        file_path: str,
        destination_dir: str,
        corrupt_chunk_index: Optional[int] = None,
    ) -> Tuple[FileTransferSession, str]:
        """Perform end-to-end chunk transfer loop with optional corruption for integrity tests."""
        session = self.orchestrator.transfer.initiate_transfer(
            source_device_id=source_id,
            target_device_id=target_id,
            file_path=file_path,
        )

        for i in range(session.total_chunks):
            data, chunk_hash = self.orchestrator.transfer.get_chunk(session.session_id, i)
            if corrupt_chunk_index is not None and i == corrupt_chunk_index:
                # Corrupt the payload
                data = b"CORRUPTED_BYTES" + data[15:]
            self.orchestrator.transfer.receive_chunk(session.session_id, i, data)

        return self.orchestrator.transfer.finalize_transfer(session.session_id, destination_dir)

    def cleanup(self) -> None:
        """Clean up temporary test database and files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
