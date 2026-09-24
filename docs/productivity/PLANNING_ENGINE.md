# Daily Planning, Capacity & Focus Mode

## 1. Daily Plan Generator
The `PlanningEngine` constructs a structured, time-blocked itinerary for the user based on active priorities, deadlines, and working capacity.

### Algorithm
1. **Fetch Ready Tasks**: Gathers all tasks in `TODO` status that are not blocked by prerequisites.
2. **Sort by Priority Score**: Multi-factor engine ranks tasks.
3. **Fit into Capacity**: Allocates tasks into 30–90 minute blocks until available hours (default 8.0 hours / 480 minutes) are reached.
4. **Overload Warnings**: If overdue + critical tasks exceed available capacity, flags a structured warning:
   > *"Warning: Critical work requires 10.5 hours, exceeding your 8.0 hour capacity by 2.5 hours. Recommended action: defer non-urgent tasks."*
5. **Acceptance Workflow**: The plan is created in `PROPOSED` status. The user can review, modify, and explicitly accept it (`POST /api/planning/daily/{id}/accept`).

---

## 2. Focus Mode Engine
When a user begins deep work on a task:
1. `FocusEngine.start_focus_session(task_id, duration_minutes)` initiates the session.
2. Sets system DND (Do Not Disturb) mode: silences non-critical desktop notifications and suppresses routine interruptions.
3. Automatically tracks time spent, notes captured, and execution artifacts.
4. Upon completion or timeout, restores normal notification level and offers to run the completion gate.
