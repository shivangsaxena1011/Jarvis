# SHIVANI Human Interface & Desktop Architecture (Phase 14)

## 1. Overview & Architectural Philosophy

SHIVANI's Human Interface unifies the entire multi-phase backend capabilities (Phases 1–13) into **one cohesive personal AI companion**. The architecture adopts a **dual-surface desktop model**:

```
+-----------------------------------------------------------------------------------+
|                            WINDOWS DESKTOP ENVIRONMENT                            |
|                                                                                   |
|  [Global Keyboard Hooks] (Ctrl+Space, Ctrl+Win+Space, Ctrl+Shift+S)               |
|                                                                                   |
|  +-----------------------------+    +------------------------------------------+  |
|  |     FLOATING ASSISTANT      |    |        SPOTLIGHT COMMAND BAR             |  |
|  |       HUD (OVERLAY)         |    |             (CTRL+SPACE)                 |  |
|  |  * Draggable Orb            |    |  * Instant launcher                      |  |
|  |  * Real-time Audio Waveform |    |  * Quick task submission                 |  |
|  |  * State badge & text       |    |  * Global search & shortcuts             |  |
|  +--------------+--------------+    +--------------------+---------------------+  |
|                 |                                        |                        |
|                 +-------------------+--------------------+                        |
|                                     |                                             |
|                                     v                                             |
|  +-----------------------------------------------------------------------------+  |
|  |                    SHIVANI WORKSPACE DASHBOARD (MAIN WINDOW)                |  |
|  |  * Conversational Assistant & Chat Stream                                   |  |
|  |  * Live Task & Step DAG Timeline                                            |  |
|  |  * Risk-Classified Human Approvals                                          |  |
|  |  * Universal Skills & Connectors Hub                                        |  |
|  |  * Knowledge OS & Graph Explorer                                            |  |
|  |  * Android Devices & Device Bridge Manager                                  |  |
|  |  * Memory, Preferences & Fact Vault                                         |  |
|  |  * Artifact Previewer & Code Inspector                                      |  |
|  |  * Diagnostics Doctor & Security Center                                     |  |
|  |  * Settings & Persona Configuration                                         |  |
|  +----------------------------------+------------------------------------------+  |
|                                     |                                             |
|  +----------------------------------+------------------------------------------+  |
|  |                    WINDOWS SYSTEM TRAY RUNNER                               |  |
|  |  * Dynamic Status Icons (Ready, Listening, Working, Approval, Locked, etc.) |  |
|  |  * Right-click Context Menu (HUD, Spotlight, Dashboard, Privacy, Stop, Exit)|  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
                                      |
                     REST / SSE / WebSockets (localhost:8000)
                                      |
+-----------------------------------------------------------------------------------+
|                           SHIVANI FASTAPI BACKEND SERVER                          |
|  * Orchestrator (Central Task DAG, ContextBuilder, Safety & Permissions)          |
|  * Assistant State Machine (14 states, Transitions, Lock & Privacy Controller)    |
|  * Audio & Voice Pipeline (Wake-word, Streaming Whisper STT, Edge TTS)            |
|  * Real-time WebSocket Event Bus Broadcast (`/ws/events`, `/events`)              |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Desktop Components

### 2.1 Desktop Shell (`apps/desktop/shell.py`)
The `DesktopShell` acts as the native window manager and lifecycle coordinator for the desktop assistant:
- Manages 4 primary window display modes: `DASHBOARD`, `HUD`, `COMMAND_BAR`, and `TRAY_ONLY`.
- Coordinates emergency stops across all background asyncio tasks, browser pages, and phone bridge commands.
- Handles privacy mode toggling (blinding camera/screen capture, muting audio ingestion).
- Handles local workstation security locking with PIN authentication.

### 2.2 System Tray Subsystem (`apps/desktop/tray.py`)
Direct Windows system tray integration via `win32gui` / `pystray`:
- **State-aware dynamic icons**:
  - `READY`: Idle state, awaiting commands.
  - `LISTENING`: Active audio stream receiving user voice.
  - `PROCESSING`: Transcribing audio, understanding intent, planning workflow DAG.
  - `WORKING`: Executing tools, computer use, browser actions, coding agents.
  - `APPROVAL`: Suspended workflow waiting for user confirmation on sensitive/high-risk actions.
  - `PAUSED` / `PRIVACY`: Privacy mode engaged; screen & mic muted.
  - `LOCKED`: Assistant locked; requires PIN to interact.
  - `OFFLINE`: Backend disconnected or degraded health state.
- **Context Menu Actions**:
  - Open Dashboard
  - Toggle Floating HUD
  - Open Spotlight Command Bar
  - Privacy Mode (Mute Mic & Blind Screen)
  - Emergency Stop (`Ctrl + Shift + S`)
  - Run Diagnostics Doctor
  - Exit Assistant

### 2.3 Assistant State Machine (`apps/desktop/server.py`)
Centralized state authority broadcasting across WebSockets and REST:
- **14 Deterministic States**: `IDLE`, `LISTENING`, `TRANSCRIBING`, `UNDERSTANDING`, `PLANNING`, `WAITING_FOR_PERMISSION`, `EXECUTING`, `VERIFYING`, `RECOVERING`, `SPEAKING`, `COMPLETED`, `FAILED`, `CANCELLED`, `OFFLINE`.
- **Atomic State Transitions**: Thread-safe state modifications with WebSocket event broadcasting to all connected surfaces.
- **Security Lock & Privacy State**: Tracks active PIN verification, privacy mode, and audio pipeline states.

---

## 3. Communication Protocols

| Protocol | Endpoint | Purpose |
| :--- | :--- | :--- |
| **REST API** | `http://localhost:8000/api/*` | CRUD operations for tasks, approvals, skills, connectors, devices, memory, knowledge, artifacts, and diagnostics. |
| **WebSocket** | `ws://localhost:8000/ws/events` | Bi-directional streaming for real-time state changes, task progress, timeline DAG updates, and approvals. |
| **Server-Sent Events**| `http://localhost:8000/events` | Unidirectional push for lightweight UI updates and event listeners. |
| **Static Assets** | `http://localhost:8000/static/*` | HTML, CSS, JavaScript, icons, and audio waveforms served directly from `apps/desktop/web/`. |
