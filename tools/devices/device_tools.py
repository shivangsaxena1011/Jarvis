"""Cross-Device & Ambient Intelligence Tools for Phase 18.

Exposes device listing, pairing, trust management, task routing, handoffs,
chunked file transfer, and global emergency stop to the Tool Registry and Orchestrator.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from core.devices.models import (
    AmbientContextState,
    DeviceTrustState,
    HandoffType,
)
from core.devices.orchestrator import DeviceOrchestrator
from security.permissions.engine import RiskLevel
from tools.base import BaseTool, ToolResult

_device_orchestrator: Optional[DeviceOrchestrator] = None


def get_device_orchestrator() -> DeviceOrchestrator:
    global _device_orchestrator
    if _device_orchestrator is None:
        _device_orchestrator = DeviceOrchestrator()
    return _device_orchestrator


def set_device_orchestrator(orchestrator: DeviceOrchestrator) -> None:
    global _device_orchestrator
    _device_orchestrator = orchestrator


class DeviceListTool(BaseTool):
    name = "device.list"
    description = "Lists all discovered, pairing, and trusted devices in Shivani's mesh."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(self, trust_state: Optional[str] = None, **kwargs: Any) -> ToolResult:
        orch = get_device_orchestrator()
        state_filter = DeviceTrustState(trust_state.lower()) if trust_state else None
        devices = orch.list_devices(trust_state=state_filter)
        return ToolResult(
            success=True,
            data={"devices": [d.to_dict() for d in devices], "total": len(devices)},
        )


class DevicePairTool(BaseTool):
    name = "device.pair"
    description = "Initiates or confirms pairing with a secondary device (Android, tablet, laptop)."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(
        self,
        action: str = "initiate",
        device_id: Optional[str] = None,
        display_name: Optional[str] = None,
        platform: str = "android",
        session_id: Optional[str] = None,
        code: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResult:
        orch = get_device_orchestrator()
        try:
            if action.lower() == "initiate":
                dev_id = device_id or f"dev-{platform}-001"
                d_name = display_name or f"Shivani {platform.capitalize()}"
                sess_id, challenge_code, sas_phrase = orch.pair_device(
                    device_id=dev_id,
                    display_name=d_name,
                    platform=platform,
                )
                return ToolResult(
                    success=True,
                    data={
                        "session_id": sess_id,
                        "code": challenge_code,
                        "sas_phrase": sas_phrase,
                        "device_id": dev_id,
                        "status": "PAIRING_INITIATED",
                    },
                )
            elif action.lower() == "confirm":
                if not session_id or not code:
                    return ToolResult(success=False, error="Both 'session_id' and 'code' are required to confirm pairing.")
                dev = orch.confirm_pairing(session_id=session_id, code=code)
                return ToolResult(
                    success=True,
                    data={"device": dev.to_dict(), "status": "PAIRING_CONFIRMED"},
                )
            else:
                return ToolResult(success=False, error=f"Unknown pairing action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeviceTrustTool(BaseTool):
    name = "device.trust"
    description = "Manages device trust states (revoke, block, permissions)."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(
        self,
        action: str,
        device_id: str,
        permissions: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> ToolResult:
        orch = get_device_orchestrator()
        act = action.lower()
        if act == "revoke":
            res = orch.revoke_device(device_id)
            return ToolResult(success=res, data={"device_id": device_id, "revoked": res})
        elif act == "block":
            res = orch.block_device(device_id)
            return ToolResult(success=res, data={"device_id": device_id, "blocked": res})
        elif act == "update_permissions":
            if not permissions:
                return ToolResult(success=False, error="Permissions list required.")
            res = orch.update_permissions(device_id, permissions)
            return ToolResult(success=res, data={"device_id": device_id, "permissions": permissions})
        else:
            return ToolResult(success=False, error=f"Unknown trust action: {action}")


class DeviceRouteTool(BaseTool):
    name = "device.route"
    description = "Evaluates capabilities and selects the optimal device for executing a task or workflow."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(
        self,
        task_description: str,
        required_capabilities: Optional[List[str]] = None,
        preferred_platform: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResult:
        orch = get_device_orchestrator()
        try:
            decision = orch.route_task(
                task_description=task_description,
                required_capabilities=required_capabilities,
                preferred_platform=preferred_platform,
            )
            return ToolResult(
                success=True,
                data={
                    "selected_device_id": decision.selected_device_id,
                    "target_platform": decision.target_platform,
                    "confidence_score": decision.confidence_score,
                    "reason": decision.reason,
                    "ranked_candidates": decision.ranked_candidates,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeviceHandoffTool(BaseTool):
    name = "device.handoff"
    description = "Initiates or manages task handoffs between devices (continue, transfer, delegate)."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(
        self,
        action: str = "create",
        handoff_id: Optional[str] = None,
        task_id: Optional[str] = None,
        title: Optional[str] = None,
        source_device_id: Optional[str] = None,
        target_device_id: Optional[str] = None,
        handoff_type: str = "continue",
        context_payload: Optional[Dict[str, Any]] = None,
        result_payload: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ToolResult:
        orch = get_device_orchestrator()
        act = action.lower()
        try:
            if act == "create":
                if not task_id or not target_device_id:
                    return ToolResult(success=False, error="'task_id' and 'target_device_id' are required.")
                src_id = source_device_id or orch.primary_device_id
                htype = HandoffType(handoff_type.lower())
                hdf = orch.initiate_handoff(
                    task_id=task_id,
                    title=title or f"Handoff task {task_id}",
                    source_device_id=src_id,
                    target_device_id=target_device_id,
                    handoff_type=htype,
                    context_payload=context_payload,
                )
                return ToolResult(success=True, data={"handoff": hdf.to_dict()})
            elif act == "accept":
                if not handoff_id or not target_device_id:
                    return ToolResult(success=False, error="'handoff_id' and 'target_device_id' required.")
                hdf = orch.accept_handoff(handoff_id, target_device_id)
                return ToolResult(success=True, data={"handoff": hdf.to_dict()})
            elif act == "complete":
                if not handoff_id:
                    return ToolResult(success=False, error="'handoff_id' required.")
                hdf = orch.complete_handoff(handoff_id, result_payload)
                return ToolResult(success=True, data={"handoff": hdf.to_dict()})
            else:
                return ToolResult(success=False, error=f"Unknown handoff action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeviceTransferFileTool(BaseTool):
    name = "device.transfer_file"
    description = "Transfers a file across paired mesh devices with SHA-256 integrity verification."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(
        self,
        target_device_id: str,
        file_path: str,
        source_device_id: Optional[str] = None,
        custom_filename: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResult:
        orch = get_device_orchestrator()
        try:
            src_id = source_device_id or orch.primary_device_id
            session = orch.transfer_file(
                source_device_id=src_id,
                target_device_id=target_device_id,
                file_path=file_path,
                custom_filename=custom_filename,
            )
            return ToolResult(success=True, data={"transfer_session": session.to_dict()})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeviceEmergencyStopTool(BaseTool):
    name = "device.emergency_stop"
    description = "Triggers an immediate global emergency stop across all connected nodes in the mesh."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(self, reason: str = "User initiated global emergency stop", **kwargs: Any) -> ToolResult:
        orch = get_device_orchestrator()
        res = orch.emergency_stop_all(reason=reason)
        return ToolResult(success=True, data=res)


class DeviceAmbientTool(BaseTool):
    name = "device.ambient"
    description = "Inspects or updates the ambient intelligence privacy state (OFF, TASK_ONLY, PROJECT, SESSION, GLOBAL)."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(self, mode: Optional[str] = None, **kwargs: Any) -> ToolResult:
        orch = get_device_orchestrator()
        try:
            if mode:
                orch.ambient.set_ambient_state(mode.lower())
            current = orch.ambient.get_ambient_state()
            audit = orch.ambient.get_audit_trail(limit=5)
            return ToolResult(
                success=True,
                data={
                    "ambient_state": current.value,
                    "zero_surveillance_active": True,
                    "recent_audit": audit,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
