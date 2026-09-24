# Projects, Context & Continuity — Personal Productivity OS

## 1. Project Management Model
Projects bind codebases, documentation, architectural decisions, requirements, blockers, and tasks into a unified context.

### Fields & Metadata
- `id`: Unique identifier (UUID).
- `name`: Human-readable name.
- `description`: Scope and objectives.
- `priority`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- `status`: `PLANNED`, `ACTIVE`, `PAUSED`, `COMPLETED`, `ARCHIVED`.
- `codebase_path`: Absolute path to the physical codebase directory.
- `repo_url`: Git remote repository URL.
- `tags`: Domain keywords.

---

## 2. Project Health Calculation
Project health is objectively assessed as `ON_TRACK`, `AT_RISK`, or `BLOCKED` based on:
1. **Critical Blockers**: Any unresolved critical blocker immediately flags health as `BLOCKED`.
2. **Overdue Critical Tasks**: Multiple overdue high/critical tasks flag health as `AT_RISK`.
3. **Stale Activity**: No recorded task progress for over 30 days triggers an inactivity alert.

---

## 3. Decision & Requirement Logs
To prevent knowledge loss across long projects:
- **Decisions**: Logged with date, title, rationale, alternatives considered, and superseding links (`supersedes_decision_id`).
- **Requirements**: Logged with status (`DRAFT`, `ACCEPTED`, `IMPLEMENTED`, `VERIFIED`), acceptance criteria, and linked tests.
- **Blockers**: Traced to specific dependencies, third parties, or environment bugs with clear root cause summaries.

---

## 4. Continuity Summaries
When returning to a project after days or weeks, invoking:
```bash
shivani project context <project_id>
```
produces a concise briefing:
- Current project health and active milestone.
- What was completed in the last active session.
- The highest priority next task ready to be worked on.
- Any active blockers requiring immediate attention.
