# SHIVANI — Phase 1 Architectural Audit

**Date**: September 24, 2026  
**Auditor**: Senior AI Systems Architect & Core Runtime Engineer  
**Status**: Foundation Established — Modular Alignment in Progress  

---

## 1. Executive Summary

This audit reviews the initial foundation built for **SHIVANI (Personal Autonomous AI Computer Agent)** against the strict product requirements of Phase 1. The existing foundation provides a robust, working async Python 3.12 runtime with Pydantic settings, a three-tier permission model, a sandboxed command validator, a redacting audit logger, an initial tool registry, and a working FastAPI + WebSocket dashboard.

To fulfill the rigorous production standard specified for Phase 1, we identify architectural enhancements, package modularization needs, and tool completeness gaps to be addressed immediately.

---

## 2. Current Architecture & Existing Features

### 2.1 Runtime & Framework Choices
- **Language & Environment**: Python 3.12.13 managed via `uv` 0.11.25. Clean virtual environment with zero bloated legacy dependencies.
- **Async API & Networking**: FastAPI + Uvicorn + HTTPX for native asynchronous I/O and low-latency HTTP/WebSocket communication.
- **Data Modeling & Validation**: Pydantic v2.13 for strongly-typed configurations, schemas, and task states.
- **Operating System Interaction**: `psutil`, `pyautogui`, `pygetwindow`, and sandboxed subprocess execution.

### 2.2 Working Modules
- **`core/config.py`**: Central typed settings from `.env`.
- **`security/permissions/engine.py`**: Three-tier risk levels (`SAFE`, `SENSITIVE`, `CRITICAL`), async approval requests, timeout expiration.
- **`security/sandbox/command_validator.py`**: Hard blocks on destructive commands (`format`, `diskpart`, `rmdir /s /q c:\`, `rm -rf /`, fork bombs) and path traversal checks.
- **`security/audit/logger.py`**: Structured JSONL audit log with regex-based credential and secret redaction.
- **`tools/base.py` & `tools/registry.py`**: Base tool interface and central registry with timeout envelopes and post-execution environmental verification.
- **`core/context/normalizer.py`**: Hindi/Hinglish vocabulary normalizer and deictic pronoun resolver.
- **`apps/desktop/server.py`**: REST API and WebSocket event streaming with a dark-first futuristic dashboard.

---

## 3. Gaps & Missing Features

1. **Structured Domain Exceptions**:
   - Lack of standard typed errors (`ProviderError`, `ToolError`, `PermissionDeniedError`, `ValidationError`, `VerificationError`, `TaskCancelledError`) with standardized fields (`code`, `task_id`, `recovery_suggestion`).
2. **Dedicated Event Bus (`core/events/`)**:
   - The current event system was coupled to WebSocket broadcasting rather than an independent in-memory Pub/Sub event bus supporting standard event types (`TASK_CREATED`, `TASK_PLANNED`, `TASK_WAITING_APPROVAL`, `TASK_STARTED`, `TOOL_STARTED`, `TOOL_COMPLETED`, `TOOL_FAILED`, `TASK_VERIFYING`, `TASK_COMPLETED`, `TASK_FAILED`, `TASK_CANCELLED`).
3. **Canonical Task Model (`core/tasks/`)**:
   - The task model needs standardization to include: `id`, `user_request`, `status`, `priority`, `created_at`, `updated_at`, `plan`, `current_step`, `result`, `error`, `requires_confirmation`, `metadata`.
4. **Provider Interface Standardization (`core/providers/`)**:
   - Moving from `core/llm/` to `core/providers/` and standardizing methods: `generate()`, `generate_structured()`, `stream()`, `health_check()`.
5. **Command Risk Classification**:
   - The terminal tool classifier should explicitly support a 4-tier model: `SAFE`, `WARNING`, `DANGEROUS`, `BLOCKED`.
6. **Missing Computer & Filesystem Tools**:
   - Computer: Need `computer.close_app`, `computer.list_windows`, and explicit `computer.active_window`.
   - Filesystem: Need `filesystem.list`, `filesystem.search`, `filesystem.read_metadata`, `filesystem.create_directory`.
   - Filesystem deletion should not be unrestricted; destructive deletion should remain withheld until full permission testing.
7. **Health & Endpoint Surface**:
   - Missing dedicated `/health` endpoint with component breakdown (`runtime`, `llm`, `tools`, `events`).
   - Missing `POST /tasks/{id}/cancel` and `GET /events` (SSE streaming).
8. **UI Controls**:
   - UI needs standard status (`IDLE`), recent activity feed, and primary controls: `[Start Listening]`, `[Stop]`, `[Settings]`, `[Task History]`.

---

## 4. Technical Debt & Risks

- **Coupling of Subsystems**: Orchestrator previously held internal tool discovery and emergency state inline. Factoring into clean sub-packages prevents monolithic growth.
- **Error Propagation**: Tools previously returned string errors inside `ToolResult.error`. Raising and catching typed domain errors provides structured recovery paths.
- **Window Enumeration Robustness**: Windows 11 window enumeration requires resilient fallback when windows are minimized or headless display servers are running.

---

## 5. Recommended Changes & Action Plan

1. Create `core/errors.py` with the full structured exception hierarchy.
2. Build `core/events/bus.py` with typed events and async subscriber queues.
3. Build `core/tasks/task.py` with canonical task attributes and state transitions.
4. Establish `core/providers/` (`base.py`, `gemini.py`, `openai.py`, `mock.py`, `factory.py`) with `health_check()`.
5. Modularize `core/planner/` and `core/executor/`.
6. Upgrade `security/sandbox/command_validator.py` to 4-tier classification (`SAFE`, `WARNING`, `DANGEROUS`, `BLOCKED`).
7. Expand `tools/computer/` and `tools/filesystem/` with the missing foundation tools.
8. Implement `/health`, `POST /tasks/{id}/cancel`, and `GET /events` in `apps/desktop/server.py`.
9. Update Desktop UI with requested status, buttons, and event timeline.
10. Add automated test coverage and verify 100% pass.
