# SHIVANI AI — Phase 15 Automation Architecture

## 1. System Overview

Phase 15 unifies proactive intelligence, scheduling, event-driven workflows, and autonomous automation under a single controlled pipeline:

```text
TRIGGER → CONTEXT → EVALUATE → PLAN → PERMISSION CHECK → EXECUTE → VERIFY → REPORT
```

Shivani performs scheduled, recurring, event-triggered, and long-running routines without requiring manual prompting for every step, while adhering to the core principle:

> **Proactive does NOT mean uncontrolled.**
> Shivani never expands its permissions autonomously, never executes high-risk operations without explicit approval, and always treats untrusted external data as DATA, not AUTHORITY.

---

## 2. Core Architectural Pillars

```
+-----------------------------------------------------------------------------------+
|                               USER INTERFACES                                     |
|  - Desktop Hub (Automations View, Cards, History, Analytics)                      |
|  - Command Bar & System Tray Notifications                                       |
|  - CLI: `shivani automation [list|create|edit|enable|disable|run|pause|resume]`  |
|  - Voice & Chat Natural Language Prompt Compiler                                  |
+-----------------------------------------+-----------------------------------------+
                                          | REST API / CLI / Tools
                                          v
+-----------------------------------------------------------------------------------+
|                         AUTOMATION ENGINE (FACADE)                                |
|  `core/automation/engine.py`                                                      |
|  - CRUD & Lifecycle: create, edit, pause, resume, enable, disable, run, delete   |
|  - Template Registry & Prompt Compiler (`core/automation/dsl.py`)                |
|  - Previews, Validation & Dry-Run Sandbox Simulation                             |
+--------------------+--------------------+--------------------+--------------------+
                     |                    |                    |
                     v                    v                    v
+-------------------------+  +-------------------------+  +-------------------------+
|     TRIGGER ENGINE      |  |    BACKGROUND WORKER    |  |    AUTOMATION RUNNER    |
| `triggers.py`           |  | `worker.py`             |  | `runner.py`             |
| - TimeTriggerEvaluator  |  | - Sleep/Wake Detection  |  | - Safe Condition Eval   |
| - EventTriggerMatcher   |  | - Battery (<20%) Yield  |  | - Scope Permission Gate |
| - Watchdog/Folder Match |  | - Catch-Up Policy Exec  |  | - Idempotency Guard     |
| - Device Event Matcher  |  | - Worker Heartbeat Loop |  | - Exponential Backoff   |
+-------------------------+  +-------------------------+  +-------------------------+
                     |                    |                    |
                     +--------------------+--------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                          SECURITY & GOVERNANCE LAYER                              |
|  - `AutomationPermissionEvaluator` (`core/automation/permissions.py`)             |
|  - `PermissionEngine` & `RiskLevel` Gating (`security/permissions/engine.py`)     |
|  - `PromptInjectionDefense` (Regex pattern scanner & untrusted data demarcation) |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                         PERSISTENCE & RECOVERY LAYER                              |
|  `core/automation/store.py` (Thread-safe SQLite Database)                         |
|  - `automations`: Full automation configuration, schedules, and permissions       |
|  - `automation_runs`: Step-by-step audit records, outputs, and errors             |
|  - `automation_versions`: Audit trail for edits and rollbacks                     |
|  - `idempotency_records`: Cryptographic hash keys to prevent duplicate execution  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Subsystem Breakdown

### 3.1 Data Models (`core/automation/models.py`)
- Strongly typed Pydantic V2 models.
- Enums: `TriggerType`, `ConditionOperator`, `LogicalOperator`, `FailurePolicy`, `AutomationStatus`, `RunStatus`, `AutomationScope`, `AutomationSource`.
- Structured schedules: `TimeSchedule` supports interval seconds, daily time of day, days of the week, standard cron syntax, and IANA timezone resolution (with fallback for Windows).
- Permissions: `AutomationPermissions` restricts capabilities, allowed path prefixes, pre-approved tools, allowed recipient domains, and maximum allowable risk tier.

### 3.2 Persistent Storage (`core/automation/store.py`)
- Resides at `~/.shivani/data/automations.db`.
- WAL-mode SQLite with thread-safe connection pooling and automatic table creation.
- Provides version history on updates for complete rollback capability and audit transparency.

### 3.3 Trigger & Event Matching (`core/automation/triggers.py`)
- **Time Triggers**: Computes exact next run timestamps using `TimeTriggerEvaluator`. Handles periodic cron calculations, intervals, and one-shot timers.
- **Event Triggers**: `EventTriggerMatcher` evaluates incoming `Event` objects against watched folder path filters, device ID patterns, and app lifecycle events.

### 3.4 Safe Condition Engine (`core/automation/conditions.py`)
- Zero `eval()`, zero `exec()`.
- Pure structured predicates (`equals`, `not_equals`, `contains`, `not_contains`, `greater_than`, `less_than`, `exists`, `is_empty`, `matches_regex`).
- Boolean logic: Recursive `AND`, `OR`, and `NOT` grouping.

### 3.5 Automation Runner (`core/automation/runner.py`)
- Enforces quiet hours policies.
- Evaluates conditions before step execution.
- Checks step permissions and requests human approval if risk level exceeds safe bounds.
- Checks and sets SHA-256 idempotency keys.
- Executes step actions via tool dispatcher with exponential backoff on retryable failures.
- Records all step run records and emits event notifications.

### 3.6 Background Worker (`core/automation/worker.py`)
- Runs continuously as a non-blocking daemon thread.
- Periodically checks for due automations.
- Monitors system sleep/wake events: calculates elapsed time and applies configured catch-up policies (`RUN_ONCE`, `SKIP`, `RUN_ALL`).
- Monitors laptop battery status via `psutil`: defers resource-heavy runs when battery < 20% and not charging.
- Automatically pauses lower-priority background tasks when high-priority interactive user tasks are active.

### 3.7 Master Facade (`core/automation/engine.py`)
- Encapsulates runner, worker, store, and template library.
- Subscribes to the system `EventBus` to handle real-time event-triggered automations.
