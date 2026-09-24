"""
SHIVANI Desktop Server
FastAPI application providing complete REST endpoints, Server-Sent Events (SSE),
and WebSockets for the Human Interface & Desktop Experience (Phase 14).
Integrates Skills, Connectors, Adapters, Devices, Knowledge OS, Memory,
Artifacts, Notifications, Security, Diagnostics, and Persona Settings.
"""

from datetime import datetime, timezone
from enum import Enum
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from core.config import get_settings
from core.orchestrator.orchestrator import Orchestrator
from core.events.bus import Event, EventType, get_event_bus
from voice.pipeline import VoicePipeline
from voice.state import get_audio_state_manager
from observability.diagnostics import DIAGNOSTICS
from observability.health import HEALTH
from observability.performance import PROFILER
from notifications.center import NotificationCategory, NotificationItem
from security.permissions.models import RiskLevel
from core.productivity.models import TaskPriority, TaskStatus

settings = get_settings()
orchestrator = Orchestrator(settings=settings)
event_bus = get_event_bus()
audio_state_mgr = get_audio_state_manager()
voice_pipeline = VoicePipeline(orchestrator=orchestrator, settings=settings)

app = FastAPI(title="SHIVANI Desktop Assistant", version="1.0.0")


# ==============================================================================
# ASSISTANT CENTRAL STATE MACHINE
# ==============================================================================

class AssistantState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    WAITING_FOR_PERMISSION = "WAITING_FOR_PERMISSION"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    SPEAKING = "SPEAKING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    OFFLINE = "OFFLINE"
    LOCKED = "LOCKED"


class AssistantStateManager:
    """Manages high-level assistant UX state, privacy mode, and lock state."""
    def __init__(self):
        self.state: AssistantState = AssistantState.IDLE
        self.privacy_mode: bool = False
        self.locked: bool = False
        self._lock_code: str = "1234"
        self.current_agent: Optional[str] = None
        self.current_step: Optional[str] = None
        self.current_task_id: Optional[str] = None
        self.persona_settings = {
            "response_style": "balanced",  # concise, balanced, detailed
            "tone": "friendly",           # professional, friendly, casual
            "language": "auto",           # auto, en, hi, hinglish
            "speaking_speed": 1.0,
            "voice_volume": 1.0,
            "theme": "dark",              # dark, light, luminous
        }

    def set_state(self, state: AssistantState, agent: Optional[str] = None, step: Optional[str] = None, task_id: Optional[str] = None):
        if self.locked and state != AssistantState.LOCKED:
            return
        self.state = state
        if agent is not None:
            self.current_agent = agent
        if step is not None:
            self.current_step = step
        if task_id is not None:
            self.current_task_id = task_id

    def toggle_privacy_mode(self, enabled: Optional[bool] = None) -> bool:
        if enabled is None:
            self.privacy_mode = not self.privacy_mode
        else:
            self.privacy_mode = enabled
        return self.privacy_mode

    def lock(self) -> None:
        self.locked = True
        self.state = AssistantState.LOCKED

    def unlock(self, code: str) -> bool:
        if code == self._lock_code:
            self.locked = False
            self.state = AssistantState.IDLE
            return True
        return False

assistant_state_mgr = AssistantStateManager()


# ==============================================================================
# WEBSOCKET & EVENT BROADCASTING
# ==============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_text(json.dumps(message))
            except Exception:
                dead.append(conn)
        for d in dead:
            self.disconnect(d)

manager = ConnectionManager()

def on_bus_event(event: Event):
    # Map event types to Assistant State transitions
    et = event.event_type
    if et == EventType.TASK_CREATED:
        assistant_state_mgr.set_state(AssistantState.UNDERSTANDING, task_id=event.task_id)
    elif et == EventType.TASK_PLANNED:
        assistant_state_mgr.set_state(AssistantState.PLANNING, task_id=event.task_id)
    elif et == EventType.TASK_WAITING_APPROVAL:
        assistant_state_mgr.set_state(AssistantState.WAITING_FOR_PERMISSION, task_id=event.task_id)
    elif et in (EventType.TASK_STARTED, EventType.TOOL_STARTED):
        agent_name = event.data.get("agent", "Orchestrator")
        action_name = event.data.get("action", event.data.get("tool", "Executing step"))
        assistant_state_mgr.set_state(AssistantState.EXECUTING, agent=agent_name, step=str(action_name), task_id=event.task_id)
    elif et == EventType.TASK_VERIFYING:
        assistant_state_mgr.set_state(AssistantState.VERIFYING, task_id=event.task_id)
    elif et == EventType.TASK_COMPLETED:
        assistant_state_mgr.set_state(AssistantState.COMPLETED, task_id=event.task_id)
    elif et == EventType.TASK_FAILED:
        assistant_state_mgr.set_state(AssistantState.FAILED, task_id=event.task_id)
    elif et == EventType.TASK_CANCELLED:
        assistant_state_mgr.set_state(AssistantState.CANCELLED, task_id=event.task_id)

    payload = {
        "event": event.event_type.value,
        "task_id": event.task_id,
        "timestamp": event.timestamp,
        "data": event.data,
        "assistant_state": assistant_state_mgr.state.value,
        "privacy_mode": assistant_state_mgr.privacy_mode,
        "locked": assistant_state_mgr.locked,
    }
    asyncio.create_task(manager.broadcast(payload))

event_bus.subscribe(on_bus_event)


# ==============================================================================
# SYSTEM & ASSISTANT STATE APIS
# ==============================================================================

@app.get("/health")
async def health_check():
    return await orchestrator.health_check()


@app.get("/status")
@app.get("/api/status")
async def get_system_status():
    pending = orchestrator.permissions.list_pending_requests()
    return {
        "status": "healthy" if not assistant_state_mgr.locked else "locked",
        "agent_name": "SHIVANI",
        "environment": settings.ENV,
        "assistant_state": assistant_state_mgr.state.value,
        "privacy_mode": assistant_state_mgr.privacy_mode,
        "locked": assistant_state_mgr.locked,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "registered_tools_count": len(orchestrator.tools.list_tools()),
        "pending_approvals_count": len(pending),
        "emergency_stop_active": orchestrator.emergency.is_stopped,
        "active_tasks_count": sum(1 for t in orchestrator._tasks.values() if t.status.value in ["PLANNING", "EXECUTING", "VERIFYING"]),
    }


class StateActionRequest(BaseModel):
    action: str  # "listen", "stop_speaking", "privacy_toggle", "lock", "unlock"
    pin: Optional[str] = None
    enabled: Optional[bool] = None


@app.post("/api/state/control")
async def control_assistant_state(req: StateActionRequest):
    if req.action == "privacy_toggle":
        new_val = assistant_state_mgr.toggle_privacy_mode(req.enabled)
        return {"privacy_mode": new_val}
    elif req.action == "lock":
        assistant_state_mgr.lock()
        return {"locked": True, "state": assistant_state_mgr.state.value}
    elif req.action == "unlock":
        if not req.pin or not assistant_state_mgr.unlock(req.pin):
            raise HTTPException(status_code=401, detail="Invalid unlock PIN")
        return {"locked": False, "state": assistant_state_mgr.state.value}
    elif req.action == "stop_speaking":
        voice_pipeline.interrupt()
        return {"interrupted": True}
    elif req.action == "listen":
        assistant_state_mgr.set_state(AssistantState.LISTENING)
        return {"state": assistant_state_mgr.state.value}
    raise HTTPException(status_code=400, detail=f"Unknown action: {req.action}")


# ==============================================================================
# TASK & CONVERSATION APIS
# ==============================================================================

class TaskSubmitOrPersonalRequest(BaseModel):
    # Execution Task fields
    user_request: Optional[str] = None
    query: Optional[str] = None
    screen_context: bool = False
    attachments: List[str] = Field(default_factory=list)

    # Personal Task fields
    title: Optional[str] = None
    description: str = ""
    priority: str = "MEDIUM"
    project_id: Optional[str] = None
    goal_id: Optional[str] = None
    milestone_id: Optional[str] = None
    due_date: Optional[str] = None
    estimated_duration_minutes: int = 30
    tags: List[str] = Field(default_factory=list)


TaskSubmitRequest = TaskSubmitOrPersonalRequest
TaskCreateRequest = TaskSubmitOrPersonalRequest


@app.post("/tasks")
@app.post("/api/tasks")
async def submit_or_create_task(req: TaskSubmitOrPersonalRequest):
    if req.title:
        priority_enum = getattr(TaskPriority, (req.priority or "MEDIUM").upper(), TaskPriority.MEDIUM)
        task = orchestrator.productivity.tasks.create_task(
            title=req.title,
            description=req.description,
            priority=priority_enum,
            project_id=req.project_id,
            goal_id=req.goal_id,
            milestone_id=req.milestone_id,
            due_date=req.due_date,
            estimated_duration_minutes=req.estimated_duration_minutes,
            tags=req.tags,
        )
        return task.model_dump()

    if assistant_state_mgr.locked:
        raise HTTPException(status_code=423, detail="Assistant is locked. Please unlock first.")

    instruction = (req.user_request or req.query or "").strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="Missing user_request or query in request body")

    if req.screen_context and not assistant_state_mgr.privacy_mode:
        instruction += " [Context: User attached current screen reference]"

    task = await orchestrator.submit_task(instruction)
    return task.model_dump()


@app.get("/tasks")
@app.get("/api/tasks")
async def list_tasks(
    limit: Optional[int] = None,
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
):
    if type == "execution" or (limit is not None and project_id is None and status is None):
        tasks = orchestrator.list_tasks(limit=limit or 20)
        return [t.model_dump() for t in tasks]

    tasks = orchestrator.productivity.store.list_tasks(project_id=project_id, status=status)
    return [t.model_dump() for t in tasks]


@app.get("/tasks/{task_id}")
@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    p_task = orchestrator.productivity.store.get_task(task_id)
    if p_task:
        return p_task.model_dump()
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.model_dump()


@app.post("/tasks/{task_id}/cancel")
@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    cancelled = orchestrator.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Task not found or not in cancellable state")
    return {"success": True, "task_id": task_id, "status": "CANCELLED"}


@app.get("/api/tasks/{task_id}/timeline")
async def get_task_timeline(task_id: str):
    """Returns chronological timeline events specifically for a task."""
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    events = [e for e in event_bus._history if e.task_id == task_id]
    steps = []
    if task.plan and task.plan.steps:
        for s in task.plan.steps:
            steps.append({
                "step_index": s.step_number,
                "description": s.description,
                "tool": s.tool_name,
                "agent": getattr(s, "agent", "Orchestrator"),
                "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            })
    return {
        "task_id": task_id,
        "query": task.user_request,
        "status": task.status.value,
        "steps": steps,
        "events": [e.model_dump() for e in events],
    }


class ConversationMessageRequest(BaseModel):
    message: str
    include_screen: bool = False
    language: Optional[str] = "auto"


@app.post("/api/conversation/message")
async def send_conversation_message(req: ConversationMessageRequest):
    if assistant_state_mgr.locked:
        raise HTTPException(status_code=423, detail="Assistant is locked.")

    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    task = await orchestrator.submit_task(user_text)
    return {
        "user_message": user_text,
        "task_id": task.id,
        "status": task.status.value,
        "reply": f"Understood. Starting task: '{user_text}'",
    }


# ==============================================================================
# APPROVALS & PERMISSION ENGINE
# ==============================================================================

class ApprovalDecisionRequest(BaseModel):
    approved: bool
    resolved_by: str = "user"
    scope: str = "once"  # "once" | "task"


@app.get("/approvals")
@app.get("/api/approvals")
async def list_approvals():
    pending = orchestrator.permissions.list_pending_requests()
    res = []
    for r in pending:
        d = r.model_dump()
        d["reversibility"] = False if r.risk_level in [RiskLevel.HIGH_RISK, RiskLevel.CRITICAL] else True
        res.append(d)
    return res


@app.post("/approvals/{request_id}")
@app.post("/api/approvals/{request_id}")
async def resolve_approval(request_id: str, req: ApprovalDecisionRequest):
    success = orchestrator.approve_request(request_id, req.approved, resolved_by=req.resolved_by)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found or already resolved")
    return {"success": True, "request_id": request_id, "approved": req.approved, "scope": req.scope}


# ==============================================================================
# UNIVERSAL SKILLS APIS (PHASE 13)
# ==============================================================================

@app.get("/api/skills")
async def list_skills():
    """Lists installed and active skills."""
    skills_meta = orchestrator.skill_registry.list_skills()
    health_map = await orchestrator.skill_registry.get_health_status()
    res = []
    for m in skills_meta:
        item = m.model_dump()
        item["health"] = health_map.get(m.name, "HEALTHY")
        res.append(item)
    return res


@app.post("/api/skills/{skill_name}/enable")
async def enable_skill(skill_name: str):
    res = await orchestrator.skill_lifecycle.enable(skill_name)
    if res.is_err:
        raise HTTPException(status_code=400, detail=res.unwrap_err())
    return {"success": True, "skill": skill_name, "status": "ACTIVE"}


@app.post("/api/skills/{skill_name}/disable")
async def disable_skill(skill_name: str):
    res = await orchestrator.skill_lifecycle.disable(skill_name)
    if res.is_err:
        raise HTTPException(status_code=400, detail=res.unwrap_err())
    return {"success": True, "skill": skill_name, "status": "DISABLED"}


class InstallSkillRequest(BaseModel):
    package_path: str
    user_confirmed: bool = False


@app.post("/api/skills/install")
async def install_skill(req: InstallSkillRequest):
    p = Path(req.package_path)
    res = await orchestrator.skill_lifecycle.install(p, user_confirmed=req.user_confirmed)
    if res.is_err:
        raise HTTPException(status_code=400, detail=res.unwrap_err())
    return {"success": True, "manifest": res.unwrap().model_dump()}


# ==============================================================================
# CONNECTORS & ACCOUNTS APIS (PHASE 13)
# ==============================================================================

@app.get("/api/connectors")
async def list_connectors():
    return orchestrator.connector_registry.list_connectors()


@app.get("/api/accounts")
async def list_accounts(provider: Optional[str] = None):
    accounts = orchestrator.account_manager.list_accounts(provider=provider)
    return [a.model_dump() for a in accounts]


class SwitchAccountRequest(BaseModel):
    provider: str
    account_id: str


@app.post("/api/accounts/switch")
async def switch_account(req: SwitchAccountRequest):
    ok = orchestrator.account_manager.switch_active_account(req.provider, req.account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Account or provider not found")
    return {"success": True, "provider": req.provider, "active_account_id": req.account_id}


# ==============================================================================
# APP ADAPTERS & DISCOVERY (PHASE 13)
# ==============================================================================

@app.get("/api/adapters")
async def list_adapters(app_type: Optional[str] = None):
    adapters = orchestrator.adapter_registry.list_adapters(app_type=app_type)
    return [{"name": a.name, "type": a.app_type} for a in adapters]


class LaunchAppRequest(BaseModel):
    name: str
    args: List[str] = Field(default_factory=list)


@app.post("/api/adapters/launch")
async def launch_app(req: LaunchAppRequest):
    adapter = orchestrator.adapter_registry.get_adapter(req.name)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Application '{req.name}' not found")
    launched = await adapter.launch(args=req.args)
    return {"success": launched, "app": req.name}


# ==============================================================================
# ANDROID DEVICES & BRIDGE APIS (PHASE 7)
# ==============================================================================

@app.get("/api/devices")
async def list_devices():
    devices = orchestrator.device_bridge.list_devices()
    return [d.model_dump() for d in devices]


@app.get("/api/devices/{device_id}/status")
async def get_device_status(device_id: str):
    stat = orchestrator.device_bridge.get_device(device_id)
    if not stat:
        raise HTTPException(status_code=404, detail="Device not found")
    return stat.model_dump()


@app.post("/api/devices/{device_id}/disconnect")
async def disconnect_device(device_id: str):
    ok = orchestrator.device_bridge.disconnect(device_id)
    return {"success": ok, "device_id": device_id}


# ==============================================================================
# KNOWLEDGE OS APIS (PHASE 12)
# ==============================================================================

@app.get("/api/knowledge/search")
async def search_knowledge(q: str = Query(..., min_length=1), limit: int = 10):
    res = orchestrator.knowledge_os.search(q, limit=limit)
    return res.get("items", [])


@app.get("/api/knowledge/projects")
async def get_knowledge_projects():
    projects = orchestrator.knowledge_os.get_projects()
    return [p.model_dump() for p in projects]


@app.get("/api/knowledge/graph")
async def query_knowledge_graph(entity: Optional[str] = None):
    data = orchestrator.knowledge_os.query_graph(entity=entity)
    return data


class AddNoteRequest(BaseModel):
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)


@app.post("/api/knowledge/notes")
async def add_knowledge_note(req: AddNoteRequest):
    note = orchestrator.knowledge_os.add_note(title=req.title, content=req.content)
    return note.model_dump()


# ==============================================================================
# MEMORY & PREFERENCES APIS (PHASE 8)
# ==============================================================================

@app.get("/api/memory/preferences")
async def get_memory_preferences():
    return orchestrator.memory.get_all_preferences()


class SetPreferenceRequest(BaseModel):
    key: str
    value: Any


@app.post("/api/memory/preferences")
async def set_memory_preference(req: SetPreferenceRequest):
    orchestrator.memory.set_preference(req.key, req.value)
    return {"success": True, "key": req.key, "value": req.value}


@app.get("/api/memory/facts")
async def search_memory_facts(q: str = ""):
    facts = orchestrator.memory.search_facts(q)
    return facts


class ForgetMemoryRequest(BaseModel):
    memory_id: str


@app.post("/api/memory/forget")
async def forget_memory(req: ForgetMemoryRequest):
    ok = orchestrator.memory.forget(req.memory_id)
    return {"success": ok, "id": req.memory_id}


# ==============================================================================
# ARTIFACT CENTER APIS (PHASE 6)
# ==============================================================================

@app.get("/api/artifacts")
async def list_artifacts(limit: int = 30):
    artifacts = orchestrator.artifact_manager.list_artifacts(limit=limit)
    return [a.model_dump() for a in artifacts]


@app.get("/api/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    art = orchestrator.artifact_manager.get_artifact(artifact_id)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")
    preview = orchestrator.artifact_manager.get_preview(artifact_id)
    return {
        "metadata": art.model_dump(),
        "preview": preview,
    }


# ==============================================================================
# NOTIFICATIONS CENTER APIS (PHASE 8)
# ==============================================================================

@app.get("/api/notifications")
async def list_notifications():
    items = orchestrator.notifications.list_notifications()
    return [item.model_dump() for item in items]


@app.post("/api/notifications/{notification_id}/dismiss")
async def dismiss_notification(notification_id: str):
    ok = orchestrator.notifications.dismiss(notification_id)
    return {"success": ok, "id": notification_id}


@app.post("/api/notifications/clear")
async def clear_notifications():
    orchestrator.notifications.clear_all()
    return {"success": True}


# ==============================================================================
# SECURITY, PRIVACY & DIAGNOSTICS APIS (PHASE 9)
# ==============================================================================

@app.get("/api/security/status")
async def get_security_status():
    return {
        "permission_policy": settings.SECURITY_POLICY,
        "privacy_mode": assistant_state_mgr.privacy_mode,
        "locked": assistant_state_mgr.locked,
        "safe_mode": orchestrator.safe_mode.is_enabled,
        "emergency_stop_available": True,
        "audit_log_path": settings.AUDIT_LOG_PATH,
        "recent_security_events": orchestrator.audit.get_recent_events(limit=10),
    }


@app.get("/api/diagnostics/run")
async def run_diagnostics(full: bool = False):
    if full:
        items = DIAGNOSTICS.run_full_doctor()
    else:
        items = DIAGNOSTICS.run_quick_doctor()
    return {
        "passed": all(item.passed or item.severity != "FAIL" for item in items),
        "items": [item.to_dict() for item in items],
    }


# ==============================================================================
# SETTINGS & PERSONA APIS
# ==============================================================================

@app.get("/api/settings")
async def get_settings_data():
    return {
        "general": {
            "env": settings.ENV,
            "wake_word": settings.WAKE_WORD,
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.LLM_MODEL,
        },
        "persona": assistant_state_mgr.persona_settings,
        "hotkeys": {
            "command_bar": "Ctrl+Space",
            "push_to_talk": "Ctrl+Shift+Space",
            "screen_context": "Ctrl+Shift+S",
            "emergency_stop": "Ctrl+Shift+X",
        },
    }


class UpdateSettingsRequest(BaseModel):
    persona: Optional[Dict[str, Any]] = None


@app.post("/api/settings")
async def update_settings_data(req: UpdateSettingsRequest):
    if req.persona:
        assistant_state_mgr.persona_settings.update(req.persona)
    return {"success": True, "settings": assistant_state_mgr.persona_settings}


# ==============================================================================
# PROACTIVE INTELLIGENCE & AUTOMATION APIS (PHASE 15)
# ==============================================================================

class CreateAutomationPromptRequest(BaseModel):
    prompt: str
    owner: str = "user"


class EditAutomationPromptRequest(BaseModel):
    prompt: str


class RunAutomationRequest(BaseModel):
    dry_run: bool = False
    context: Dict[str, Any] = Field(default_factory=dict)


@app.get("/api/automations")
async def list_automations(status: Optional[str] = None):
    from core.automation.models import AutomationStatus
    stat = None
    if status:
        try:
            stat = AutomationStatus(status.upper())
        except ValueError:
            pass
    automations = orchestrator.automation.list_automations(status=stat)
    return [a.model_dump() for a in automations]


@app.post("/api/automations")
async def create_automation(auto_data: Dict[str, Any]):
    from core.automation.dsl import AutomationDSL
    ok, errors, auto = AutomationDSL.validate_automation(auto_data)
    if not ok or not auto:
        raise HTTPException(status_code=400, detail={"errors": errors})
    saved = orchestrator.automation.create_automation(auto)
    return saved.model_dump()


@app.post("/api/automations/create_prompt")
async def create_automation_from_prompt(req: CreateAutomationPromptRequest):
    auto = orchestrator.automation.create_from_prompt(req.prompt, owner=req.owner)
    preview = orchestrator.automation.preview_automation(auto)
    return {
        "success": True,
        "automation": auto.model_dump(),
        "preview": preview,
    }


@app.get("/api/automations/templates")
async def get_automation_templates():
    templates = orchestrator.automation.get_templates()
    return [t.model_dump() for t in templates]


@app.get("/api/automations/analytics")
async def get_automation_analytics():
    return orchestrator.automation.get_analytics()


@app.get("/api/automations/history")
async def get_automation_history(limit: int = 50):
    runs = orchestrator.automation.get_history(limit=limit)
    return [r.model_dump() for r in runs]


@app.post("/api/automations/preview")
async def preview_automation(data: Dict[str, Any]):
    return orchestrator.automation.preview_automation(data)


@app.post("/api/automations/validate")
async def validate_automation(data: Dict[str, Any]):
    from core.automation.dsl import AutomationDSL
    ok, errs, auto = AutomationDSL.validate_automation(data)
    return {"valid": ok, "errors": errs, "name": auto.name if auto else None}


@app.get("/api/automations/{automation_id}")
async def get_automation(automation_id: str):
    auto = orchestrator.automation.get_automation(automation_id)
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")
    return auto.model_dump()


@app.post("/api/automations/{automation_id}/run")
async def run_automation(automation_id: str, req: RunAutomationRequest = RunAutomationRequest()):
    run = await orchestrator.automation.run_automation_now(
        automation_id, trigger_context=req.context, dry_run=req.dry_run
    )
    if not run:
        raise HTTPException(status_code=404, detail="Automation not found")
    return run.model_dump()


@app.post("/api/automations/{automation_id}/pause")
async def pause_automation(automation_id: str):
    ok = orchestrator.automation.pause_automation(automation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Automation not found")
    return {"success": True, "automation_id": automation_id, "status": "PAUSED"}


@app.post("/api/automations/{automation_id}/resume")
async def resume_automation(automation_id: str):
    ok = orchestrator.automation.resume_automation(automation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Automation not found")
    return {"success": True, "automation_id": automation_id, "status": "ACTIVE"}


@app.post("/api/automations/{automation_id}/edit")
async def edit_automation(automation_id: str, req: EditAutomationPromptRequest):
    updated = orchestrator.automation.edit_from_prompt(automation_id, req.prompt)
    if not updated:
        raise HTTPException(status_code=404, detail="Automation not found")
    return updated.model_dump()


@app.delete("/api/automations/{automation_id}")
async def delete_automation(automation_id: str):
    ok = orchestrator.automation.delete_automation(automation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Automation not found")
    return {"success": True, "automation_id": automation_id}


@app.get("/api/automations/{automation_id}/history")
async def get_single_automation_history(automation_id: str, limit: int = 50):
    runs = orchestrator.automation.get_history(automation_id=automation_id, limit=limit)
    return [r.model_dump() for r in runs]


# ==============================================================================
# EMERGENCY STOP & AUDIT
# ==============================================================================

@app.post("/stop")
@app.post("/api/stop")
async def emergency_stop():
    count = orchestrator.stop_all()
    assistant_state_mgr.set_state(AssistantState.CANCELLED)
    voice_pipeline.interrupt()
    return {"success": True, "tasks_cancelled": count, "message": "Emergency Stop Triggered"}


@app.get("/tools")
@app.get("/api/tools")
async def list_tools():
    return orchestrator.tools.list_tools()


@app.get("/audit")
@app.get("/api/audit")
async def get_audit_events(limit: int = 50):
    return orchestrator.audit.get_recent_events(limit=limit)


# ==============================================================================
# VOICE & AUDIO PIPELINE
# ==============================================================================

@app.get("/api/voice/status")
async def get_voice_status():
    return {
        "audio_state": audio_state_mgr.current_state.value,
        "assistant_state": assistant_state_mgr.state.value,
        "wake_word": settings.WAKE_WORD,
        "stt_provider": settings.STT_PROVIDER,
        "stt_model": settings.STT_MODEL,
        "tts_provider": settings.TTS_PROVIDER,
        "tts_voice": settings.TTS_VOICE,
        "is_speaking": voice_pipeline.tts.is_speaking(),
        "privacy_mode": assistant_state_mgr.privacy_mode,
    }


@app.post("/api/voice/interact")
async def voice_interact(request: Request):
    if assistant_state_mgr.privacy_mode:
        raise HTTPException(status_code=403, detail="Voice interaction blocked: Privacy Mode is active.")
    if assistant_state_mgr.locked:
        raise HTTPException(status_code=423, detail="Assistant is locked.")

    audio_bytes = await request.body()
    if not audio_bytes or len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Empty or invalid audio stream payload")

    assistant_state_mgr.set_state(AssistantState.TRANSCRIBING)
    result = await voice_pipeline.process_spoken_instruction(
        audio_data=audio_bytes,
        sample_rate=16000,
        play_tts_response=True
    )
    return result


@app.post("/api/voice/stop")
async def voice_stop():
    voice_pipeline.interrupt()
    assistant_state_mgr.set_state(AssistantState.IDLE)
    return {"success": True, "interrupted": True}


class TTSRequest(BaseModel):
    text: str


@app.post("/api/voice/tts")
async def voice_tts(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    assistant_state_mgr.set_state(AssistantState.SPEAKING)
    res = await voice_pipeline.tts.speak(req.text, play_audio=False)
    audio_filename = Path(res.audio_path).name if res.audio_path else None
    return {
        "text": res.text,
        "audio_url": f"/api/voice/audio/{audio_filename}" if audio_filename else None,
        "duration_seconds": res.duration_seconds
    }


@app.get("/api/voice/audio/{filename}")
async def get_voice_audio(filename: str):
    file_path = Path(settings.AUDIO_OUTPUT_DIR) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")


# ==============================================================================
# PHASE 16: PRODUCTIVITY OS REST ENDPOINTS
# ==============================================================================

class TaskCompleteRequest(BaseModel):
    notes: str = ""
    artifact_path: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    name: str
    description: str = ""
    priority: str = "MEDIUM"
    codebase_path: Optional[str] = None
    repo_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class GoalCreateRequest(BaseModel):
    title: str
    description: str = ""
    category: str = "General"
    priority: str = "MEDIUM"
    target_date: Optional[str] = None


class FocusStartRequest(BaseModel):
    task_id: Optional[str] = None
    task_title: str = ""
    duration_minutes: int = 60


class DailyPlanRequest(BaseModel):
    date: Optional[str] = None
    available_hours: float = 8.0


@app.get("/api/productivity/dashboard")
async def get_productivity_dashboard():
    return orchestrator.productivity.get_dashboard_summary()


@app.post("/api/tasks/{task_id}/complete")
async def complete_task(task_id: str, req: TaskCompleteRequest):
    exec_output = {"manually_confirmed": True, "notes": req.notes}
    if req.artifact_path:
        exec_output["artifact_path"] = req.artifact_path

    verified, failures = orchestrator.productivity.tasks.complete_task(
        task_id, execution_output=exec_output
    )
    if not verified:
        raise HTTPException(status_code=400, detail=f"Completion gate rejected: {'; '.join(failures)}")
    task = orchestrator.productivity.store.get_task(task_id)
    return task.model_dump()


@app.post("/api/tasks/{task_id}/defer")
async def defer_task(task_id: str, req: Dict[str, Any]):
    task = orchestrator.productivity.store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.DEFERRED
    if "new_due_date" in req:
        task.due_date = req["new_due_date"]
    orchestrator.productivity.store.save_task(task)
    return task.model_dump()


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    success = orchestrator.productivity.store.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}


# Projects
@app.get("/api/projects")
async def list_projects(status: Optional[str] = None):
    projects = orchestrator.productivity.store.list_projects(status=status)
    return [p.model_dump() for p in projects]


@app.post("/api/projects")
async def create_project(req: ProjectCreateRequest):
    priority_enum = getattr(TaskPriority, req.priority.upper(), TaskPriority.MEDIUM)
    project = orchestrator.productivity.projects.create_project(
        name=req.name,
        description=req.description,
        priority=priority_enum,
        codebase_path=req.codebase_path,
        repo_url=req.repo_url,
        tags=req.tags,
    )
    return project.model_dump()


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    project = orchestrator.productivity.store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.model_dump()


@app.get("/api/projects/{project_id}/context")
async def get_project_context(project_id: str):
    return orchestrator.productivity.context.get_project_context(project_id)


@app.get("/api/projects/{project_id}/health")
async def get_project_health(project_id: str):
    return orchestrator.productivity.projects.get_project_health(project_id)


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    success = orchestrator.productivity.store.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True}


# Goals
@app.get("/api/goals")
async def list_goals(status: Optional[str] = None):
    goals = orchestrator.productivity.store.list_goals(status=status)
    return [g.model_dump() for g in goals]


@app.post("/api/goals")
async def create_goal(req: GoalCreateRequest):
    priority_enum = getattr(TaskPriority, req.priority.upper(), TaskPriority.MEDIUM)
    goal = orchestrator.productivity.goals.create_goal(
        title=req.title,
        description=req.description,
        category=req.category,
        priority=priority_enum,
        target_date=req.target_date,
    )
    return goal.model_dump()


@app.get("/api/goals/{goal_id}/progress")
async def get_goal_progress(goal_id: str):
    goal = orchestrator.productivity.goals.update_goal_progress(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"goal_id": goal.id, "title": goal.title, "progress": goal.progress, "status": goal.status.value}


# Planning & Recommendations
@app.post("/api/planning/daily")
async def generate_daily_plan(req: DailyPlanRequest):
    plan, warning = orchestrator.productivity.planning.generate_daily_plan(
        date_str=req.date,
        available_minutes=int(req.available_hours * 60),
    )
    return {"plan": plan.model_dump(), "warning": warning}


@app.post("/api/planning/daily/{plan_id}/accept")
async def accept_daily_plan(plan_id: str):
    success = orchestrator.productivity.planning.accept_plan(plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"success": True}


@app.get("/api/planning/recommend")
async def recommend_tasks(limit: int = 3):
    return orchestrator.productivity.recommend_next_tasks(limit=limit)


@app.get("/api/planning/weekly")
async def weekly_review():
    return orchestrator.productivity.reviews.generate_weekly_review()


# Focus Mode
@app.post("/api/focus/start")
async def start_focus(req: FocusStartRequest):
    session = orchestrator.productivity.focus.start_focus_session(
        task_id=req.task_id,
        task_title=req.task_title,
        duration_minutes=req.duration_minutes,
    )
    return session.model_dump()


@app.post("/api/focus/end")
async def end_focus(req: Dict[str, Any]):
    completed = req.get("completed", True)
    notes = req.get("notes", "")
    session = orchestrator.productivity.focus.end_focus_session(completed=completed, notes=notes)
    if not session:
        return {"active": False, "message": "No active focus session to end"}
    return session.model_dump()


@app.get("/api/focus/active")
async def get_active_focus():
    active = orchestrator.productivity.focus.active_session
    return {"active": active is not None, "session": active.model_dump() if active else None}


# ==============================================================================
# WEBSOCKET & SSE STREAMING
# ==============================================================================

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state snapshot on connect
        await websocket.send_text(json.dumps({
            "event": "SNAPSHOT",
            "assistant_state": assistant_state_mgr.state.value,
            "privacy_mode": assistant_state_mgr.privacy_mode,
            "locked": assistant_state_mgr.locked,
            "tools_count": len(orchestrator.tools.list_tools()),
            "tasks_count": len(orchestrator._tasks),
        }))
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                if action == "stop":
                    orchestrator.stop_all()
                    voice_pipeline.interrupt()
                elif action == "ping":
                    await websocket.send_text(json.dumps({"event": "PONG"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/events")
async def sse_events(request: Request):
    queue = event_bus.create_subscription_queue()

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                event: Event = await queue.get()
                payload = {
                    "event": event.event_type.value,
                    "task_id": event.task_id,
                    "timestamp": event.timestamp,
                    "data": event.data,
                    "assistant_state": assistant_state_mgr.state.value,
                }
                yield f"data: {json.dumps(payload)}\n\n"
        finally:
            event_bus.remove_subscription_queue(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==============================================================================
# STATIC ASSETS & INDEX
# ==============================================================================

web_dir = Path(__file__).parent / "web"
web_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


@app.get("/")
async def serve_index():
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "SHIVANI Desktop Agent is running. Web UI not found."}
