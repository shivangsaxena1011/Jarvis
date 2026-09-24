# SHIVANI Phase 15 System Audit: Proactive Intelligence, Routines, Scheduling & Autonomous Automation

## 1. System Audit & Inventory of Previous Phases (Phases 1–14)

### 1.1 Existing Subsystems Audited

| Subsystem | Existing Implementation & Capabilities | Reusability Assessment & Phase 15 Integration |
| :--- | :--- | :--- |
| **Scheduler** (`core/scheduler/scheduler.py`) | In-memory `SchedulerService` with `ScheduledJob`, interval/once scheduling, basic SHA-256 state idempotency, and `execute_due(runner_callback)`. | **Core Extension Target**: Upgrade into a persistent, timezone-aware (`Asia/Kolkata` / configurable) scheduler supporting cron expressions, one-time future timestamps, quiet hours, and sleep/wake reconciliation without breaking Phase 8 tools (`tools/scheduler/`). |
| **Task Engine** (`core/tasks/task.py`, `core/tasks/manager.py`, `core/tasks/executor.py`) | Deterministic Task DAG, `Task`, `PlanStep`, `TaskPlan`, status tracking (`PENDING`, `PLANNING`, `EXECUTING`, `VERIFYING`, `COMPLETED`, `FAILED`, etc.), verification callbacks. | **DO NOT DUPLICATE**: Automation workflows will compile directly into or execute through the unified Task DAG / Workflow Engine. |
| **Workflow Engine** (`core/workflows/engine.py`, `models.py`) | Composable cross-app workflows (`Workflow`, `WorkflowStep`, `WorkflowResult`), checkpointing at stages, variable passing, approval pauses. | **Directly Reusable**: Automation execution runs directly leverage `Workflow` and `WorkflowEngine` for multi-step orchestrations. |
| **Permission Engine** (`security/permissions/engine.py`, `models.py`) | 5-tier risk hierarchy (`SAFE`, `LOW_RISK`, `SENSITIVE`, `HIGH_RISK`, `CRITICAL`), policy modes (`lenient`, `standard`, `strict`), approval futures, session pre-approvals (`{task_id}:{tool_name}`). | **DO NOT DUPLICATE**: Automations declare scoped capabilities and maximum risk levels. Any action exceeding the automation's risk limit or policy triggers `request_approval`. |
| **Event Bus** (`core/events/bus.py`) | Asynchronous pub/sub event bus with `EventType` enumeration, listener callbacks, queue subscriptions, and history buffer. | **Event Trigger Source**: Automations subscribe to system events (`TASK_COMPLETED`, `TOOL_COMPLETED`, file system changes, device connections). |
| **Notification Center** (`notifications/center.py`) | Central notification hub with categories (`INFO`, `SUCCESS`, `WARNING`, `ACTION_REQUIRED`, `ERROR`), priority routing, and listeners. | **Reporting & Quiet Hours**: Automations emit human-readable progress and completion notifications respecting user quiet hour windows. |
| **Device Bridge** (`core/bridge/device_bridge.py`) | Android device manager handling pairing, tokens, heartbeat, status, and command routing (`launch_app`, `notifications`, `clipboard`). | **Cross-Device Triggers**: Triggers on `device_connected` / `device_disconnected` and executes cross-device actions (e.g. transfer artifact to phone). |
| **Resource Manager** (`core/concurrency/resource_manager.py`) | Mutual exclusion locks for files, git repos, mobile bridges, and browser sessions. | **Conflict Prevention**: Concurrent background automations acquire scoped resource locks to prevent colliding with active user sessions. |
| **Recovery Engine** (`recovery/checkpoint_manager.py`, `recovery_engine.py`) | Checkpoint persistence for in-progress tasks (`TaskCheckpoint`), recovery on restart, rollback management. | **Automation Checkpointing**: Long-running background workflows save step checkpoints for resumption after crash or network drop. |
| **Observability & Health** (`observability/health.py`, `diagnostics.py`) | System diagnostics, CPU/RAM performance monitoring, component health checks. | **Resource Budgeting**: Background execution throttles or defers execution during low battery (<20%) or extreme system load. |
| **Desktop UI & API** (`apps/desktop/server.py`, `web/`) | 66 REST endpoints, WebSocket `/ws/events`, Floating HUD, Spotlight Command Bar, Dashboard with capability views. | **Automation Center UI**: Add dedicated Automation Center views, Visual Automation Builder, and REST APIs (`/api/automations/*`). |

---

## 2. Gap Analysis & Missing Capabilities

1. **Persistent Automation Store**: Existing `SchedulerService` is purely in-memory; jobs are lost when the process terminates. Phase 15 requires an SQLite-backed `AutomationStore` persisting across restarts.
2. **Advanced Schedule Triggers**: Existing scheduler only supports simple `interval_seconds`. Phase 15 requires cron-like patterns (`Every day at 8 AM`, `Every weekday`, `Every Monday`, `Every 30 minutes`, specific calendar dates) with timezone support (`Asia/Kolkata`).
3. **Event-Based Triggers**: Triggers reacting to internal state changes (task completion, artifact generation, device connection, build failure, file changes in watched directories).
4. **Structured Condition Engine**: Evaluates `IF ... THEN` rules with safe structured predicates (`equals`, `contains`, `greater_than`, `exists`, etc.) and composite boolean operators (`AND`, `OR`, `NOT`). No arbitrary code execution.
5. **Automation DSL & Natural Language Compiler**: Translates user voice or text (`"Every weekday at 8 AM summarize my unread emails"`) into validated, typed automation specifications with preview, explanation, and dry-run capability.
6. **Scoped Automation Permissions & Privilege Escalation Defenses**: Each automation is assigned explicit boundaries (`allowed_capabilities`, `allowed_accounts`, `allowed_devices`, `allowed_applications`, `allowed_file_paths`, `max_risk_level`). Untrusted external content (e.g. web search or email content) is classified as data, never instruction authority (prompt injection defense).
7. **Background Worker & Sleep/Wake Reconciliation**: An autonomous background runner that checks due schedules, detects missed executions caused by laptop sleep/hibernation, and applies catch-up policies (`run_latest`, `skip_if_missed`).
8. **Idempotency & Retry Architecture**: Tracks `idempotency_key` per step to prevent duplicate executions (duplicate emails, double social posts, duplicate files). Configurable failure policies (`STOP`, `RETRY`, `SKIP_STEP`, `PAUSE_FOR_USER`, `CONTINUE_WITH_WARNING`).
9. **Automation Dashboard & Visual Builder**: Intuitive UI in the desktop dashboard allowing users to inspect active automations, view real-time execution cards, construct automations visually, and browse safe pre-configured templates.
10. **Unified CLI**: CLI interface (`shivani automation list`, `create`, `enable`, `disable`, `run`, `pause`, `resume`, `history`, `doctor`).

---

## 3. Architecture Conflicts & Resolutions

| Potential Conflict | Risk | Architectural Resolution |
| :--- | :--- | :--- |
| **Scheduler Duplication** | Creating an independent scheduler could cause desynchronization with `tools/scheduler/` and `Orchestrator.scheduler`. | **Unified Architecture**: Extend `core/scheduler/scheduler.py` or inherit `SchedulerService` into `AutomationEngine`, maintaining 100% backwards compatibility while providing persistent cron, event triggers, and condition checks. |
| **Permission Bypass** | Background automations running unattended might bypass human confirmation for dangerous actions. | **Strict Gating**: Automations inherit the same `PermissionEngine`. High-risk actions (`terminal_execute`, file deletions, social publishing) MUST pause in `WAITING_FOR_PERMISSION` and post to the Approval Queue unless explicitly pre-authorized within strict narrow scopes. |
| **Task Engine Duplication** | Creating a separate execution engine for automations would diverge from the `TaskExecutor` and `WorkflowEngine`. | **Reuse Task Engine**: The `AutomationEngine` delegates step execution to `Orchestrator.submit_task` or `WorkflowEngine.execute_workflow`, ensuring complete parity in tool verification, audit logging, and state events. |
| **Resource Contention** | Multiple background automations executing simultaneously could freeze the computer or conflict with foreground user actions. | **Resource Manager Integration**: Background tasks use `ResourceManager` locks and run with background priority, yielding immediately to interactive user commands. |

---

## 4. Implementation Plan & Package Structure

```text
core/automation/
├── __init__.py                # Package exports
├── models.py                  # Pydantic models: Automation, Trigger, Condition, Step, Run, History
├── store.py                   # Persistent SQLite storage for automations and execution history
├── triggers.py                # Time triggers (cron, interval, once, timezone) & Event triggers
├── conditions.py              # Structured condition evaluation engine (AND/OR/NOT predicates)
├── permissions.py             # Scoped permission evaluator & prompt injection defenses
├── dsl.py                     # DSL schemas, validation, natural language compiler & dry-run sandbox
├── runner.py                  # Workflow runner, retry policy, failure handling, idempotency
├── worker.py                  # Persistent background worker daemon, sleep/wake reconciliation
├── templates.py               # Safe pre-built automation templates (Morning Brief, GitHub Monitor, etc.)
└── engine.py                  # Central AutomationEngine coordinating registry, scheduler, and worker
```

Additionally:
- Extend `core/orchestrator/orchestrator.py` to initialize `self.automation = AutomationEngine(orchestrator=self)`.
- Extend `apps/desktop/server.py` with REST endpoints for `/api/automations/*`.
- Extend `apps/desktop/web/` with the Automation Center view, template cards, and visual builder.
- Add `cli/automation_cli.py` and register it in `cli/main.py`.
- Create comprehensive tests in `tests/automation/`.
- Author complete documentation in `docs/automation/`.
