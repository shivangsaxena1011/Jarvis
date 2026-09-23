# System Architecture — SHIVANI

## Architectural Philosophy

SHIVANI is built upon the core loop: **OBSERVE → PLAN → ACT → VERIFY**.

Unlike standard chatbots or simplistic prompt wrappers, SHIVANI:
1. Gathers sensory and environment context before planning.
2. Formulates formal task graphs with explicit arguments, timeouts, and expected outcomes.
3. Checks every step against a rigorous Permission Engine (`SAFE`, `SENSITIVE`, `CRITICAL`).
4. Executes operations through well-defined, schema-validated tool implementations.
5. Verifies side-effects in the actual target environment (processes, files, windows, DOM states).
6. Employs automated recovery strategies when expectations are not met.
7. Records an immutable, redacting audit trail for security review.

---

## High-Level Topology

```
                  ┌───────────────────────────────┐
                  │       User Interaction        │
                  │ (Voice Audio / Web Dashboard) │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │      Context & Normalizer     │
                  │  (Hinglish, History, Window)  │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │       Agent Orchestrator      │
                  │     (Task State Machine)      │
                  └───────────────┬───────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Task Planner    │      │ Permission      │      │ Emergency Stop  │
│ (LLM Provider)  │      │ Engine          │      │ Controller      │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │        Action Executor        │
                  │ (Tool Registry, Observe/Act)  │
                  └───────────────┬───────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Computer Tools  │      │ Filesystem      │      │ Terminal /      │
│ & Windows UI    │      │ Controlled Ops  │      │ Shell Tools     │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │      Verification Engine      │
                  │ (Detect Process, Size, Delta) │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │ Redacting Audit Log & Events  │
                  │   (WebSocket / audit.jsonl)   │
                  └───────────────────────────────┘
```

---

## Core Subsystems

### 1. Task State Machine
Tasks transition through explicit lifecycle states:
- `PENDING`: Initial registration upon user request.
- `PLANNING`: Semantic interpretation, context resolution, and LLM decomposition.
- `WAITING_FOR_PERMISSION`: Suspended execution awaiting user approval for SENSITIVE or CRITICAL actions.
- `EXECUTING`: Tool dispatch with active timeout protection.
- `VERIFYING`: Evaluating physical environment indicators post-execution.
- `RECOVERING`: Attempting alternate tools or selector rollbacks.
- `COMPLETED`: All step assertions verified.
- `FAILED`: Unrecoverable error or timeout.
- `CANCELLED`: Aborted via Emergency Stop.

### 2. Context & Hinglish Engine
Maintains environment awareness:
- Current active process and foreground window title.
- Current active workspace file or directory path.
- Resolves deictic referents (*"ye wala"*, *"isko"*, *"this one"*) to the current focused item.
- Normalizes vernacular action verbs (*"kholo"*, *"chalao"*, *"band karo"*, *"clean karo"*) into structured intentions.

### 3. Permission Engine
Separates tool operations into three risk domains:
- **SAFE**: Non-invasive read actions (`computer.screenshot`, `filesystem.list_dir`).
- **SENSITIVE**: State changes in the workspace (`filesystem.write_file`, `terminal.execute` standard commands).
- **CRITICAL**: Irreversible operations (`filesystem.safe_delete`, mass process termination).
