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
from voice.pipeline import VoicePipeline
from voice.state import get_audio_state_manager

settings = get_settings()
orchestrator = Orchestrator(settings=settings)
event_bus = get_event_bus()
audio_state_mgr = get_audio_state_manager()
voice_pipeline = VoicePipeline(orchestrator=orchestrator, settings=settings)

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


# ==============================================================================
# VOICE & AUDIO PIPELINE ENDPOINTS
# ==============================================================================

@app.get("/api/voice/status")
async def get_voice_status():
    return {
        "audio_state": audio_state_mgr.current_state.value,
        "wake_word": settings.WAKE_WORD,
        "stt_provider": settings.STT_PROVIDER,
        "stt_model": settings.STT_MODEL,
        "tts_provider": settings.TTS_PROVIDER,
        "tts_voice": settings.TTS_VOICE,
        "is_speaking": voice_pipeline.tts.is_speaking(),
    }


@app.post("/api/voice/interact")
async def voice_interact(request: Request):
    """
    Receives raw audio recorded by desktop client or browser MediaRecorder,
    processes via STT -> Orchestrator -> TTS, and returns execution result.
    """
    audio_bytes = await request.body()
    if not audio_bytes or len(audio_bytes) < 100:
        raise HTTPException(status_code=400, detail="Empty or invalid audio stream payload")

    result = await voice_pipeline.process_spoken_instruction(
        audio_data=audio_bytes,
        sample_rate=16000,
        play_tts_response=True
    )
    return result


@app.post("/api/voice/stop")
async def voice_stop():
    """Immediately halts any playing TTS speech and aborts active task."""
    voice_pipeline.interrupt()
    return {"success": True, "interrupted": True}


class TTSRequest(BaseModel):
    text: str


@app.post("/api/voice/tts")
async def voice_tts(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
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
