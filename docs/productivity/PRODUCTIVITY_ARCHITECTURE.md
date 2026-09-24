# SHIVANI AI — Phase 16: Productivity OS Architecture

## 1. Overview & Vision
The **Productivity OS** elevates Shivani from an assistant that merely executes individual tasks to an **intelligent personal operating system**. It provides persistent memory and structural awareness for the user's high-level goals, ongoing projects, tasks, milestones, deadlines, blockers, decisions, and daily focus.

Shivani serves as a decision-support system:
- **Transparent Criteria**: Every recommendation, priority score, and scheduled time block explains *why* it was prioritized.
- **Human Authority**: Shivani suggests schedules and breaks down projects, but never silently reschedules commitments or marks work complete without verified proof or explicit confirmation.
- **Single Source of Truth**: Unified SQLite storage (`data/productivity.db`) in WAL mode eliminates duplicate stores and maintains data consistency across CLI, Desktop UI, background automation, and agent reasoning.

---

## 2. Architecture & Subsystem Diagram

```text
                               ┌────────────────────────────────────────────────────────┐
                               │                    HUMAN INTERFACES                    │
                               │  Desktop UI (Web/HUD) │ CLI (`shivani task/project`)   │
                               └───────────────────────┬────────────────────────────────┘
                                                       │
                                                       ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       PRODUCTIVITY ORCHESTRATOR                                       │
│                                  (core/productivity/orchestrator.py)                                  │
├───────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────────┤
│   Goal Manager    │  Project Manager  │   Task Manager    │  Priority Engine  │    Planning Engine    │
│  (Milestones,     │ (Context, Health, │  (NLP Parser,     │  (Multi-factor,   │   (Time Blocks,       │
│   Rollup Progress)│  Decisions, Blk)  │   Dependencies)   │   Why-Surfaced)   │    Capacity Checks)   │
├───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────────┤
│ Dependency Engine │  Deadline Engine  │   Focus Engine    │   Review Engine   │   Verification Gate   │
│  (DAG Graph,      │  (Date Parsing,   │ (DND Suppression, │ (Weekly/Monthly,  │  (Deliverables,       │
│   Cycle Detect)   │   Conflict Alerts)│  Session Tracking)│  Retrospectives)  │   Tests, Confirmation)│
└───────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────────┘
                                                       │
                                                       ▼
                               ┌────────────────────────────────────────────────────────┐
                               │                 UNIFIED STORAGE LAYER                  │
                               │              `data/productivity.db` (WAL)              │
                               │  [Goals] [Milestones] [Projects] [Tasks] [Decisions]   │
                               │  [Requirements] [Blockers] [FocusSessions] [Plans]     │
                               └────────────────────────────────────────────────────────┘
```

---

## 3. Subsystem Breakdown

### 3.1 Unified Storage (`core/productivity/store.py`)
- SQLite database configured with Write-Ahead Logging (`PRAGMA journal_mode=WAL`), foreign keys enabled, and indexed entity fields.
- Complete thread safety via connection pooling and scoped locks.
- Zero duplication: completely replaces ad-hoc JSON files and unifies all project/task tracking.

### 3.2 Task Intelligence & Dependency DAG (`core/productivity/dependency_engine.py`)
- Represents task relationships as a Directed Acyclic Graph (DAG).
- Proactive cycle detection prevents deadlocks (`detect_cycles(task_id, depends_on)`).
- Blocker propagation: when a prerequisite task is blocked, downstream tasks automatically inherit blocked status.
- Topological sorting determines exact execution order along the critical path.

### 3.3 Multi-Factor Priority Engine (`core/productivity/priority_engine.py`)
Calculates dynamic priority scores (`0.0` to `100.0`) based on:
1. Base Priority Weight (Critical=40, High=30, Medium=20, Low=10)
2. Deadline Proximity (Overdue=+35, Today=+25, 3-day window=+15)
3. Dependency Impact (Unblocks N downstream tasks=+5 per task)
4. Project Priority (Bonus for active high-priority projects)
5. Effort vs. Available Focus Factor
6. Clear, human-readable rationale explanation for every recommendation (`why_surfaced`).

### 3.4 Context Engine & Project Boundary Isolation (`core/productivity/context_engine.py`)
- Preserves active project state, recent decisions, open milestones, and modified files.
- Generates natural project continuity summaries ("Continue my OCR project").
- **Strict Boundary Safety**: Rejects agent actions targeting files or repositories outside the designated project boundaries without explicit confirmation.
- Detects stale project contexts (>30 days since last activity) and prompts for archive or reactivation.

### 3.5 Completion Gate (`core/productivity/verification_gate.py`)
- Never marks a task complete merely because an LLM or subagent emitted "Done".
- Requires at least one verifiable proof:
  1. Verifiable deliverable file/artifact verified on disk.
  2. Passing automated test suite.
  3. Explicit manual confirmation by the user.

---

## 4. Agent & Orchestrator Integration
The `ProductivityOrchestrator` integrates directly into the root `Orchestrator` (`core/orchestrator/orchestrator.py`), and registers a dedicated `ProjectAgent` (`agents/project/project_agent.py`) capable of breaking down project goals and orchestrating cross-agent handoffs between Research, Coding, and Presentation agents.
