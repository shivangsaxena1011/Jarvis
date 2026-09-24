# SHIVANI AI — PHASE 14 UI AUDIT & ARCHITECTURE SPECIFICATION

**Document Version:** 1.0.0  
**Phase:** 14 — Human Interface, Desktop Experience & Conversational Assistant UX  
**Repository State:** Verified Phases 1–13 Complete (288 / 288 tests passing)

---

## 1. Existing UI & Desktop Subsystems Audit

### 1.1 Desktop Application & Web Layer
- **Location:** `apps/desktop/`
- **Server:** `apps/desktop/server.py` (FastAPI, Uvicorn, port 8000).
- **Web Frontend:** `apps/desktop/web/` (`index.html`, `app.js`, `style.css`).
- **Communication:**
  - REST API (`/health`, `/status`, `/tools`, `/tasks`, `/approvals`, `/stop`, `/audit`, `/api/voice/*`).
  - WebSocket (`/ws/events`).
  - Server-Sent Events (`/events`).
- **Current UI Coverage:**
  - Simple 2-column layout (Command Input + Active Task on left; Timeline list on right).
  - Rudimentary task progress indicator and approval card.
  - Basic voice trigger button and emergency stop.
- **Identified Gaps in Current UI:**
  - No Floating Assistant HUD mode.
  - No Global Command Bar (modal / hotkey triggered).
  - No System Tray integration (cannot run in background or minimize to tray).
  - Missing conversational multi-turn chat stream.
  - Missing views for: Skills, App Connectors, Multi-Account contexts, Knowledge OS / Graph, Memory facts, Android Devices, Artifact Previews, Security / Privacy controls, Diagnostics Doctor, Settings / Persona, and Multimodal upload.
  - Missing offline / degraded state indicator.
  - Missing keyboard accessibility, theme switching (Light / Dark / Luminous), and multi-monitor awareness.

---

## 2. Reusable Backend Capabilities & Endpoints

| Subsystem | Existing Python Backend Core | Existing API in `server.py` | Required Extension in Phase 14 |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | `Orchestrator` (`submit_task`, `list_tasks`, `cancel_task`, `stop_all`) | `/tasks`, `/tasks/{id}`, `/tasks/{id}/cancel`, `/stop` | Context-aware follow-up, resume, screen-context injection |
| **Voice & Speech** | `VoicePipeline`, `AudioStateManager`, `EdgeTTS`, `Whisper` | `/api/voice/status`, `/api/voice/interact`, `/api/voice/stop`, `/api/voice/tts` | Real-time wake word state synchronization, push-to-talk endpoint, barge-in speech interruption |
| **Approvals & Risk**| `PermissionEngine`, `RiskLevel` (SAFE, LOW, SENSITIVE, HIGH, CRITICAL) | `/approvals`, `/approvals/{id}` | Structured risk display, target preview, diff details, batch approve |
| **Notifications** | `NotificationCenter` (INFO, SUCCESS, WARNING, ACTION_REQUIRED, ERROR) | None | `/api/notifications`, `/api/notifications/{id}/dismiss`, `/api/notifications/clear` |
| **Universal Skills** | `SkillRegistry`, `SkillLifecycleManager` (Phase 13) | None | `/api/skills`, `/api/skills/{name}/enable`, `/api/skills/{name}/disable`, `/api/skills/install` |
| **Connectors & Accts**| `ConnectorRegistry`, `AccountManager` (Phase 13) | None | `/api/connectors`, `/api/accounts`, `/api/accounts/switch` |
| **Adapters** | `AdapterRegistry`, `AppDiscovery` (Phase 13) | None | `/api/adapters`, `/api/adapters/launch` |
| **Knowledge OS** | `KnowledgeOS`, `ASTCodeGraph`, `HybridRAG` (Phase 12) | None | `/api/knowledge/search`, `/api/knowledge/projects`, `/api/knowledge/graph`, `/api/knowledge/notes` |
| **Memory** | `MemoryManager` (Preferences, episodic, facts) (Phase 8) | None | `/api/memory/search`, `/api/memory/preferences`, `/api/memory/forget` |
| **Android Bridge** | `DeviceBridge`, `PhoneAgent` (Phase 7) | None | `/api/devices`, `/api/devices/{id}/status`, `/api/devices/pair`, `/api/devices/disconnect` |
| **Artifacts** | `ArtifactManager` (Phase 6) | None | `/api/artifacts`, `/api/artifacts/{id}`, `/api/artifacts/{id}/download` |
| **Security & Privacy**| `AuditLogger`, `PromptInjection`, `SafeModeController` (Phase 9) | `/audit` | `/api/security/status`, `/api/security/privacy-mode`, `/api/security/lock`, `/api/security/unlock` |
| **Recovery** | `RecoveryEngine`, Checkpoints (Phase 9) | None | `/api/recovery/checkpoints`, `/api/recovery/resume/{id}` |
| **Diagnostics** | `DIAGNOSTICS`, `HEALTH`, `PROFILER` | `/health`, `/status` | `/api/diagnostics/run`, `/api/diagnostics/report` |
| **Config & Settings**| `Settings`, `AppDirectories` | None | `/api/settings`, `/api/settings/update` |

---

## 3. Recommended Architectural Design

### 3.1 Dual-Surface Desktop Shell Architecture
To give the user complete freedom without resource bloat:
1. **Desktop Shell (`apps/desktop/shell.py`)**:
   - System Tray integration using `pystray` / Windows Shell NotifyIcon or native fallback.
   - Global Hotkeys (`Ctrl + Space` for Command Bar, `Ctrl + Shift + Space` for Push-to-Talk, `Ctrl + Shift + X` for Stop, `Ctrl + Shift + S` for Screen Context).
   - Window Mode Management:
     - `Dashboard`: Full multi-panel view.
     - `HUD`: Lightweight, draggable, floating pill showing assistant state and quick mic/text input.
     - `CommandBar`: Spotlight-style overlay input.
     - `Tray`: Minimized background listening mode.
2. **Server-Side API Upgrades (`apps/desktop/server.py`)**:
   - Add all missing REST endpoints cleanly categorized under `/api/*`.
   - Enhance WebSocket `/ws/events` to broadcast voice states (`LISTENING`, `THINKING`, `SPEAKING`), notifications, and task lifecycle events.
3. **Modular Frontend Client (`apps/desktop/web/`)**:
   - State-driven reactive frontend with view switcher.
   - Dedicated modules:
     - Assistant HUD & Command Bar
     - Conversational Chat & Task Progress Cards
     - Live Task Timeline & Agent Visibility
     - Approvals & Risk Dialogs
     - Knowledge & Project Explorer
     - Memory Inspector
     - Universal Skills Marketplace / Manager
     - Android Device Companion
     - Connected Accounts & Connectors
     - Artifact Previews (Presentation, Research, Code, Notes)
     - Security, Privacy Mode & Lock Mode
     - Diagnostics Doctor
     - Persona & System Settings
     - Accessibility & Themes (Dark, Light, Luminous)

---

## 4. Implementation Steps & Verification Plan

1. **Backend API Extension in `apps/desktop/server.py`**:
   - Expose endpoints for Skills, Connectors, Accounts, Adapters, Knowledge, Memory, Devices, Artifacts, Notifications, Security, Diagnostics, and Settings.
2. **Desktop Shell & System Tray (`apps/desktop/shell.py` & `apps/desktop/tray.py`)**:
   - Implement background shell, tray icon state updates (`Ready`, `Listening`, `Working`, `Approval Required`, `Offline`, `Locked`), and global hotkey daemon.
3. **Polished Desktop Frontend (`apps/desktop/web/`)**:
   - Restructure `index.html`, `style.css`, and modular JavaScript controller into clean, componentized architecture.
   - Implement HUD, Command Bar, Conversational view, and 12 dedicated feature centers.
   - Full theme support (Dark, Light, Luminous) and accessibility enhancements (keyboard navigation, ARIA semantics).
4. **Comprehensive Test Suite (`tests/ui/`)**:
   - Unit tests for API endpoints in `server.py`.
   - State machine tests for Assistant states (`IDLE`, `LISTENING`, `PLANNING`, `EXECUTING`, `WAITING_APPROVAL`, `SPEAKING`, etc.).
   - Tray and shell state synchronization tests.
   - E2E acceptance tests for all 8 prompt scenarios (Chrome open, OCR research, LinkedIn draft approval, Emergency Stop, Restart Recovery, Device Disconnect, Offline mode, High-risk operation).
5. **Documentation & Final Verification**:
   - Complete documentation in `docs/ui/`.
   - Verify 100% test pass rate across all 288 + new UI tests.
