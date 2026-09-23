"""
SHIVANI Desktop Server
FastAPI application providing REST endpoints and WebSockets for the Desktop UI.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.config import get_settings
from core.orchestrator.orchestrator import Orchestrator

settings = get_settings()
orchestrator = Orchestrator(settings=settings)

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
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

# Hook orchestrator events to WebSocket broadcast
def on_orchestrator_event(event_type: str, data: Dict[str, Any]):
    asyncio.create_task(manager.broadcast({"event": event_type, "data": data}))

orchestrator.add_event_listener(on_orchestrator_event)


class TaskSubmitRequest(BaseModel):
    query: str


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    resolved_by: str = "user"


@app.get("/api/status")
async def get_system_status():
    pending_approvals = orchestrator.permissions.list_pending_requests()
    return {
        "status": "healthy",
        "agent_name": "SHIVANI",
        "environment": settings.ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "registered_tools_count": len(orchestrator.tools.list_tools()),
        "pending_approvals_count": len(pending_approvals),
        "emergency_stop_active": orchestrator.emergency.is_stopped,
    }


@app.get("/api/tools")
async def list_tools():
    return orchestrator.tools.list_tools()


@app.post("/api/tasks")
async def submit_task(req: TaskSubmitRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    task = await orchestrator.submit_task(req.query)
    return task.model_dump()


@app.get("/api/tasks")
async def list_tasks(limit: int = 20):
    tasks = orchestrator.list_tasks(limit=limit)
    return [t.model_dump() for t in tasks]


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.model_dump()


@app.get("/api/approvals")
async def list_approvals():
    return [r.model_dump() for r in orchestrator.permissions.list_pending_requests()]


@app.post("/api/approvals/{request_id}")
async def resolve_approval(request_id: str, req: ApprovalDecisionRequest):
    success = orchestrator.approve_request(request_id, req.approved, resolved_by=req.resolved_by)
    if not success:
        raise HTTPException(status_code=404, detail="Approval request not found or already resolved")
    return {"success": True, "request_id": request_id, "approved": req.approved}


@app.post("/api/stop")
async def emergency_stop():
    count = orchestrator.stop_all()
    return {"success": True, "tasks_cancelled": count, "message": "Emergency Stop Triggered"}


@app.get("/api/audit")
async def get_audit_events(limit: int = 50):
    return orchestrator.audit.get_recent_events(limit=limit)


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming client commands over WS if any
            try:
                msg = json.loads(data)
                if msg.get("action") == "stop":
                    orchestrator.stop_all()
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Mount UI static files
web_dir = Path(__file__).parent / "web"
web_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


@app.get("/")
async def serve_index():
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "SHIVANI Desktop API is running. Web UI not found."}
