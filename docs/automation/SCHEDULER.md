# SHIVANI Unified Persistent Scheduler

## 1. Unified Scheduling Architecture

To prevent split-brain execution loops, Phase 15 unifies all timer and recurring routine execution into a single persistent scheduler (`core/automation/triggers.py` & `core/automation/worker.py`), deprecating isolated in-memory timers.

---

## 2. Schedule Evaluation Engine

The `TimeTriggerEvaluator` manages schedule calculations:

### 2.1 Interval Schedules
- Calculates `next_run = now + interval_seconds`.
- Supports jitter to prevent "thundering herd" problems when multiple automations have identical intervals.

### 2.2 Daily / Time-of-Day Schedules
- Parses target time (e.g. `08:30`).
- If today's target time has already passed in the target timezone, advances to the next valid day in `days_of_week`.
- Accommodates weekend filtering (e.g., `days_of_week: [0, 1, 2, 3, 4]`).

### 2.3 Cron Schedules
- Evaluates 5-field cron syntax (`minute hour dom month dow`).
- Handles wildcard expressions, ranges (`1-5`), and step intervals (`*/15`).

### 2.4 One-Time Timers
- Supports exact ISO-8601 timestamps.
- Automatically marks the automation as `DISABLED` or deletes it after successful execution.

---

## 3. Persistent State & Due Detection

The scheduler stores the computed `next_run` in the SQLite database:
1. Every tick (default: 5 seconds), the background worker queries for enabled automations where `next_run <= now_utc`.
2. When an automation is selected, the scheduler atomically marks it as running to prevent duplicate triggers across threads.
3. Upon run completion or failure, the scheduler calculates the subsequent `next_run` and updates the database record.
