# Goals & Milestones — Personal Productivity OS

## 1. Goal Lifecycle
Goals represent high-level user objectives across personal, professional, and technical dimensions.

### Status Transitions
- `PLANNED`: Initial draft state.
- `ACTIVE`: Currently being pursued with active milestones and tasks.
- `ON_HOLD`: Temporarily paused; tasks are excluded from daily planning.
- `ACHIEVED`: All key milestones completed, deliverables verified.
- `ABANDONED`: Explicitly discontinued by the user.

---

## 2. Milestone Decomposition & Safeguards
When the user asks Shivani to plan a goal (e.g., *"Help me launch my SaaS product in 6 months"*):
1. **Proposal Mode**: The `GoalManager` proposes a set of milestone breakdowns with suggested criteria and dates.
2. **User Consent**: Shivani **never silently generates dozens of unreviewed tasks** into the user's task database. Milestones must be accepted before task decomposition occurs.
3. **Objective Progress Rollup**: Goal progress is not an arbitrary estimate. It is mathematically calculated by `ProgressEngine` from the verified completion ratio of its linked milestones and subtasks.

---

## 3. CLI & API Usage

### CLI
```bash
# List all active goals
shivani goal list

# Create a new goal
shivani goal create --title "Ship Phase 16 Productivity OS" --category "Engineering" --target-date "2026-10-01"

# Check verified progress
shivani goal progress <goal_id>
```

### REST API
- `GET /api/goals`: List goals (optional filter `?status=ACTIVE`).
- `POST /api/goals`: Create goal (`{"title": "...", "priority": "HIGH", "target_date": "..."}`).
- `GET /api/goals/{id}/progress`: Returns verified percentage progress and linked milestone statuses.
