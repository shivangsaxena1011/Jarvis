# Personal Tasks & Natural Language Intelligence

## 1. Unified Task Model
A `PersonalTask` represents an actionable item with rich metadata:
- `id`: Unique UUID.
- `title`: Short summary.
- `description`: Detailed specification or acceptance criteria.
- `priority`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- `status`: `TODO`, `IN_PROGRESS`, `BLOCKED`, `COMPLETED`, `DEFERRED`, `CANCELLED`.
- `project_id`, `goal_id`, `milestone_id`: Relational links.
- `due_date`: RFC3339 / ISO date string.
- `estimated_duration_minutes`: Expected focus time.
- `depends_on`: List of prerequisite task IDs.
- `blocking_reasons`: List of active blocker explanations.
- `tags`: Categories and contextual labels.

---

## 2. Natural Language Parser
The `TaskManager.parse_natural_language_task` engine extracts:
1. **Title**: The core actionable statement (e.g. *"Review PR #42"*).
2. **Priority**: Detected keywords like `urgent`, `asap`, `p0`, `critical`, `important`, `low priority`.
3. **Deadlines**: Relative expressions like `today`, `tomorrow`, `by Friday`, `by next Monday`, `in 3 days`.
4. **Estimated Duration**: Expressions like `30 mins`, `1 hour`, `45m`, `2h`.
5. **Project Associations**: Mentions like `for project X`, `in project Y`.

### Examples
- `"Review pull request 42 for project Alpha by tomorrow at 5pm urgent"`
  - Title: `Review pull request 42`
  - Project: `Alpha`
  - Due: Tomorrow (resolved to exact ISO date)
  - Priority: `CRITICAL`
  - Duration: 30 min (default)

---

## 3. Conversational Reference Resolution
Shivani maintains task conversational context across turns:
- `"Mark that as done"` -> Identifies the currently active or last referenced task, prompts for or checks verification artifacts, and updates status.
- `"Move it to next Monday"` -> Resolves the relative date and reschedules the active task.
- `"What is blocking it?"` -> Explains the blocker or prerequisite dependency graph for the active task.

---

## 4. Batching Similar Tasks
The `TaskManager.find_batching_opportunities` utility clusters small tasks (<30 minutes) sharing identical tags or project scopes (e.g. batching administrative emails, documentation updates, or code review passes) to minimize context switching overhead.
