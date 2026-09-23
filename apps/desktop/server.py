"""
SHIVANI Desktop Server
FastAPI application providing REST endpoints, Server-Sent Events (SSE), and WebSockets.
Listens on localhost by default for security.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from core.config import get_settings
from core.orchestrator.orchestrator import Orchestrator
from core.events.bus import Event, get_event_bus

settings = get_settings()
orchestrator = Orchestrator(settings=settings)
event_bus = get_event_bus()

app = FastAPI(title="SHIVANI Desktop Agent", version="0.1.0")

# WebSocket connection manager
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

# Hook event bus to WebSocket broadcast
def on_bus_event(event: Event):
    payload = {
        "event": event.event_type.value,
        "task_id": event.task_id,
        "timestamp": event.timestamp,
        "data": event.data
    }
    asyncio.create_task(manager.broadcast(payload))

event_bus.subscribe(on_bus_event)


class TaskSubmitRequest(BaseModel):
    user_request: Optional[str] = None
    query: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    resolved_by: str = "user"


@app.get("/health")
async def health_check():
    """System health inspection returning status across runtime, LLM, tools, and events."""
    return await orchestrator.health_check()


@app.get("/status")
@app.get("/api/status")
async def get_system_status():
    pending = orchestrator.permissions.list_pending_requests()
    return {
        "status": "healthy",
        "agent_name": "SHIVANI",
        "environment": settings.ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "registered_tools_count": len(orchestrator.tools.list_tools()),
        "pending_approvals_count": len(pending),
        "emergency_stop_active": orchestrator.emergency.is_stopped,
    }


@app.get("/tools")
@app.get("/api/tools")
async def list_tools():
    return orchestrator.tools.list_tools()


@app.post("/tasks")
@app.post("/api/tasks")
async def submit_task(req: TaskSubmitRequest):
    instruction = (req.user_request or req.query or "").strip()
    if not instruction:
        raise HTTPException(status_code=400, detail="Missing user_request or query in request body")
    task = await orchestrator.submit_task(instruction)
    return task.model_dump()


@app.get("/tasks")
@app.get("/api/tasks")
async def list_tasks(limit: int = 20):
    tasks = orchestrator.list_tasks(limit=limit)
    return [t.model_dump() for t in tasks]


@app.get("/tasks/{task_id}")
@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
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


@app.get("/events")
async def sse_events(request: Request):
    """Server-Sent Events (SSE) stream endpoint."""
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
                    "data": event.data
                }
                yield f"data: {json.dumps(payload)}\n\n"
        finally:
            event_bus.remove_subscription_queue(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/approvals")
@app.get("/api/approvals")
async def list_approvals():
    return [r.model_dump() for r in orchestrator.permissions.list_pending_requests()]


@app.post("/approvals/{request_id}")
@app.post("/api/approvals/{request_id}")
async def resolve_approval(request_id: str, req: ApprovalDecisionRequest):
    success = orchestrator.approve_request(request_id, req.approved, resolved_by=req.resolved_by)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found or already resolved")
    return {"success": True, "request_id": request_id, "approved": req.approved}


@app.post("/stop")
@app.post("/api/stop")
async def emergency_stop():
    count = orchestrator.stop_all()
    return {"success": True, "tasks_cancelled": count, "message": "Emergency Stop Triggered"}


@app.get("/audit")
@app.get("/api/audit")
async def get_audit_events(limit: int = 50):
    return orchestrator.audit.get_recent_events(limit=limit)


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "stop":
                    orchestrator.stop_all()
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Static assets
web_dir = Path(__file__).parent / "web"
web_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


@app.get("/")
async def serve_index():
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "SHIVANI Desktop Agent is running. Web UI not found."}
