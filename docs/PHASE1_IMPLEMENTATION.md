# SHIVANI — Phase 1 Implementation Guide

**Document**: Phase 1 Foundation + Core Agent Runtime  
**Status**: Completed and Verified  
**Runtime**: Python 3.12+ (CPython 3.12.13)  

---

## 1. System Architecture & Modular Layout

SHIVANI is built using modular packages adhering to clean boundary interfaces:

```
shivanI/
├── apps/
│   ├── desktop/
│   │   ├── server.py             # FastAPI REST & SSE / WebSocket server
│   │   └── web/                  # Futuristic Desktop Dashboard (HTML/CSS/JS)
│   └── mobile/                   # Android companion architecture specs
├── core/
│   ├── errors.py                 # Structured error hierarchy (ShivaniError, etc.)
│   ├── config.py                 # Pydantic Settings & environment validation
│   ├── context/
│   │   └── normalizer.py         # Hinglish/Hindi parser & deictic pronoun resolver
│   ├── events/
│   │   ├── bus.py                # Asynchronous Pub/Sub EventBus & typed events
│   │   └── __init__.py
│   ├── tasks/
│   │   ├── task.py               # Canonical Task model, TaskStatus, TaskPlan
│   │   └── __init__.py
│   ├── providers/
│   │   ├── base.py               # LLMProvider interface with health_check
│   │   ├── gemini.py             # Google Gemini REST provider
│   │   ├── openai.py             # OpenAI compatible provider
│   │   ├── mock.py               # Deterministic test provider
│   │   └── factory.py            # Dynamic model provider factory
│   ├── planner/
│   │   └── planner.py            # Task decomposition & confirmation analysis
│   ├── executor/
│   │   └── executor.py           # Step execution with rollback hooks & verification
│   └── orchestrator/
│       ├── emergency.py          # Emergency Stop controller
│       ├── orchestrator.py       # Central pipeline coordinator
│       └── state_machine.py      # Task state machine
├── security/
│   ├── permissions/
│   │   └── engine.py             # Three-tier risk levels (SAFE, SENSITIVE, CRITICAL)
│   ├── sandbox/
│   │   └── command_validator.py  # 4-tier CommandRisk (SAFE, WARNING, DANGEROUS, BLOCKED)
│   └── audit/
│       └── logger.py             # Structured JSONL logger with secret redaction
├── tools/
│   ├── base.py                   # Tool interface with validate_input, execute, verify, rollback
│   ├── registry.py               # Central registry with timeout & verification
│   ├── computer/
│   │   └── system_tools.py       # open_app, close_app, screenshot, active_window, list_windows
│   ├── filesystem/
│   │   └── file_tools.py         # list, search, read_metadata, create_directory, read, write
│   └── terminal/
│       └── shell_tools.py        # Sandboxed terminal execution tool
├── tests/                        # 28 passing unit & integration tests
├── docs/                         # Specifications & audit documentation
├── pyproject.toml                # Dependencies & build configuration
├── .env.example                  # Environment configuration template
└── main.py                       # CLI and server runtime entrypoint
```

---

## 2. Core Components Implemented

### 2.1 Task Model (`core/tasks/task.py`)
- Standardized fields: `id`, `user_request`, `status`, `priority`, `created_at`, `updated_at`, `plan`, `current_step`, `result`, `error`, `requires_confirmation`, `metadata`.
- Lifecycle statuses: `PENDING`, `PLANNING`, `WAITING_FOR_PERMISSION`, `EXECUTING`, `VERIFYING`, `RECOVERING`, `COMPLETED`, `FAILED`, `CANCELLED`.

### 2.2 Event Bus (`core/events/bus.py`)
- Supported event types: `TASK_CREATED`, `TASK_PLANNED`, `TASK_WAITING_APPROVAL`, `TASK_STARTED`, `TOOL_STARTED`, `TOOL_COMPLETED`, `TOOL_FAILED`, `TASK_VERIFYING`, `TASK_COMPLETED`, `TASK_FAILED`, `TASK_CANCELLED`, `SYSTEM_STATUS`.
- Subscriber queues for Server-Sent Events (SSE) and WebSocket broadcasting.

### 2.3 Structured Errors (`core/errors.py`)
- `ShivaniError`: Base class with `code`, `message`, `task_id`, `recovery_suggestion`, `details`.
- `ProviderError`, `ToolError`, `PermissionDeniedError`, `ValidationError`, `VerificationError`, `TaskCancelledError`.

### 2.4 Command Risk Classifier (`security/sandbox/command_validator.py`)
- **SAFE**: Read-only observation (`dir`, `echo`, `type`, `where`, `git status`).
- **WARNING**: Non-destructive workspace operations (`pip install`, `git commit`, `python script.py`).
- **DANGEROUS**: Deletions, process kills, or script injections (`del`, `rm`, `taskkill`, `Invoke-Expression`).
- **BLOCKED**: Hard-blocked destructive operations (`format`, `diskpart`, `rmdir /s /q c:\`, `rm -rf /`, fork bombs).

### 2.5 Computer & Filesystem Tool Suite
- `computer.open_app`: Launches applications with path and executable resolution; verifies process in system table.
- `computer.close_app`: Gracefully terminates processes by name or PID; verifies process exit.
- `computer.screenshot`: Captures desktop screen; verifies image bytes on disk.
- `computer.active_window`: Inspects foreground window title and process.
- `computer.list_windows`: Enumerates open windows with titles and visibility.
- `filesystem.list`: Lists directory contents with system directory shields.
- `filesystem.search`: Recursively searches files by glob pattern within workspace boundaries.
- `filesystem.read_metadata`: Returns file/dir stat, permissions, and timestamps.
- `filesystem.create_directory`: Safely creates folders with parent directory support.
- `terminal.execute`: Sandboxed shell execution with timeout and returncode verification.

---

## 3. Local API & Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Component health breakdown (`runtime`, `llm`, `tools`, `event_bus`) |
| `GET` | `/status` | Agent name, active provider, tool count, pending approvals |
| `GET` | `/tools` | List registered tools and their JSON schemas |
| `POST` | `/tasks` | Submit new user task (`user_request` or `query`) |
| `GET` | `/tasks` | List recent tasks and status |
| `GET` | `/tasks/{id}` | Retrieve specific task state and step verification results |
| `POST` | `/tasks/{id}/cancel` | Abort a pending or in-flight task |
| `GET` | `/events` | Server-Sent Events (SSE) live event stream |
| `GET` | `/approvals` | List pending approval requests |
| `POST` | `/approvals/{id}` | Approve or reject a sensitive/critical tool action |
| `POST` | `/stop` | Emergency Stop aborting all active tasks |
| `GET` | `/audit` | Retrieve structured audit events |
| `WS` | `/ws/events` | Bi-directional WebSocket event streaming |

---

## 4. How to Run & Verify

### Run Automated Test Suite
```powershell
.venv\Scripts\pytest.exe -v
```
All 28 tests will execute and pass in ~1.1 seconds.

### Launch Server & Futuristic Dashboard
```powershell
.venv\Scripts\python.exe main.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

### Execute Demo Task via CLI
```powershell
.venv\Scripts\python.exe main.py --task "Open Chrome"
```
Or with Hindi instruction:
```powershell
.venv\Scripts\python.exe main.py --task "Shivani, screenshot capture karo"
```

### Validate Setup (Dry-Run)
```powershell
.venv\Scripts\python.exe main.py --dry-run
```
