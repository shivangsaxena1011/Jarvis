# SHIVANI AI — Phase 16 Productivity OS Subsystem Audit

## 1. Executive Summary

This audit assesses the current state of SHIVANI across Phases 1–15, identifies reusable abstractions, establishes boundary guidelines to prevent duplicate task/project data stores, and designs the architecture for the **Personal Productivity Operating System (Phase 16)**.

---

## 2. Inventory of Existing Subsystems & Reusability Assessment

| Subsystem | Existing Implementation | Reusability in Phase 16 | Phase 16 Extension Required |
|---|---|---|---|
| **Task System** | `core/tasks/task.py` (`Task`, `TaskPlan`, `PlanStep`, `StepExecutionResult`) | **High**: Reusable as runtime execution unit for agent runs. Currently in-memory transient execution tasks. | Needs a persistent personal task model (`PersonalTask`) with dependencies, due dates, project/goal links, estimation, and completion gates. Runtime agent tasks map directly to execution steps of personal tasks. |
| **Project System** | `core/projects/indexer.py` (`ProjectMetadata`, code analysis, git status) | **High**: Reusable for inspecting physical local workspaces, git branches, language identification, and run commands. | Needs a first-class conceptual `Project` model linking goals, milestones, tasks, documents, decisions, blockers, and timelines. |
| **Knowledge OS** | `knowledge/` (KnowledgeGraph, Hybrid Retrieval, Entity relations) | **High**: Reusable for cross-project contextual search, entity relationships, and provenance tracking. | Index productivity entities (Projects, Goals, Decisions, Requirements) into Knowledge OS graph. |
| **Memory** | `memory/` (Episodic, Semantic, Preferences, TaskMemory) | **High**: Reusable for user preferences (working hours, focus preferences, project associations). | Record project decisions, milestones, and retrospective summaries in project-scoped memory with provenance. |
| **Planner & DAG** | `core/planner/planner.py`, `core/agents/decomposer.py` (`TaskDAG`, `SubTask`) | **High**: Reusable for task breakdown, topological sorting, and dependency evaluation. | Connect to `DependencyEngine` to detect circular dependencies and compute critical path. |
| **Automation Engine** | `core/automation/` (`AutomationEngine`, `AutomationRunner`, persistent schedules) | **High**: Reusable for scheduled routines (morning briefs, reviews, task reminders, event triggers). | Connect tasks with automations (e.g. task completion triggers automation). |
| **Integrations** | `integrations/github`, `integrations/gmail`, `tools/integrations/` | **High**: Reusable for project repo status, email tasks, and PR tracking. | Ground project continuity and GitHub status directly in real API calls; calendar availability checks. |
| **Desktop UI** | `apps/desktop/web/` (HUD, Command Bar, Views) | **High**: Reusable navigation, SSE event streaming, modular tab architecture. | Add dedicated Views: Tasks, Projects, Goals, Planning, Focus Mode, Insights. |
| **Security & Permissions** | `security/permissions/engine.py`, `AutomationPermissionEvaluator` | **High**: Reusable for high-risk gating and capability scoping. | Enforce cross-project isolation, require explicit confirmation before touching files in a project, and strictly verify task completion gates. |

---

## 3. Database & Storage Strategy: Zero Duplication

> **Rule: Do not create duplicate task databases.**

### Current Storage Map:
- `data/memory.db`: SQLite database for memory items (episodic, semantic, preferences).
- `data/knowledge/`: SQLite + Chroma vector store for knowledge nodes and edges.
- `~/.shivani/data/automations.db`: SQLite for automation routines, runs, and idempotency.
- In-memory `orchestrator._tasks`: Runtime ephemeral execution tasks for tool dispatch.

### Phase 16 Storage Design:
The unified productivity persistence layer will reside in `data/productivity.db` (WAL SQLite, thread-safe):
- `goals`: Structured goals with milestones and progress metrics.
- `milestones`: Structured milestones linked to goals and projects.
- `projects`: First-class projects with owners, repositories, and context.
- `tasks`: Robust personal tasks (`TODO`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`, etc.) with dependencies, effort estimates, and project links.
- `decisions`: Architectural and project decisions with rationale and supersession trail.
- `requirements`: Requirements traceability (`REQ -> Design -> Implementation -> Test -> Artifact`).
- `blockers`: Project blockers traced to dependencies or external issues.
- `focus_sessions`: Work logs and interruptions.
- `daily_plans`: Generated and user-accepted day schedules.

When an agent executes work for a task, the ephemeral runtime `core.tasks.Task` is spawned and its results feed into the completion gate of the persistent `core.productivity.Task`.

---

## 4. Subsystem Components & Modules to Implement

```
core/productivity/
├── models.py                  # Pydantic models for Goal, Milestone, Project, Task, Decision, Requirement, Blocker, FocusSession, DailyPlan
├── store.py                   # Thread-safe SQLite store for all productivity entities
├── goal_manager.py            # GoalManager: CRUD, milestone tracking, progress computation
├── project_manager.py         # ProjectManager: Context builder, repository links, health, retrospective
├── task_manager.py            # TaskManager: Natural language parsing, status transitions, batching
├── priority_engine.py         # PriorityEngine: Multi-factor ranking (urgency, importance, deadline, blockers, user prefs)
├── deadline_engine.py         # DeadlineEngine: Due dates, overdue detection, timezone-aware grouping
├── dependency_engine.py       # DependencyEngine: DAG graph, circular dependency check, blocker propagation
├── planning_engine.py         # PlanningEngine: Daily schedule generation, weekly review, capacity/available hours check
├── focus_engine.py            # FocusEngine: Focus mode controller, notification suppression, session tracking
├── context_engine.py          # ContextEngine: Active project context, cross-project isolation, stale context detection
├── review_engine.py           # ReviewEngine: Weekly and monthly factual reviews, project retrospectives
├── progress_engine.py         # ProgressEngine: Objective metric/milestone-driven progress calculation
├── verification_gate.py       # CompletionGate: Artifact and test verification before marking complete
├── orchestrator.py            # ProductivityOrchestrator: Master coordinator uniting all productivity engines
└── __init__.py                # Package exports
```

---

## 5. Security & Boundary Architecture

1. **Assistance vs. Autonomy**: Shivani proposes daily plans, task breakdowns, and batching, but **never makes life decisions or silently reschedules commitments without user approval**.
2. **Personal Data Isolation**: Productivity data is strictly decoupled from credentials and secrets.
3. **No Psychological Inferences**: Activity logs are strictly factual productivity metrics—never used to infer emotional, mental, or medical states.
4. **Project Confinement**: Cross-project actions require explicit confirmation. Coding actions require confirmation of the target codebase.
5. **Prompt Injection Defense**: Task descriptions or external data from GitHub/emails cannot execute privileged commands or alter security policies.
