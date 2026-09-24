# SHIVANI Automation Triggers & Event Detection

## 1. Supported Trigger Types

The trigger subsystem in `core/automation/triggers.py` supports four distinct activation modes:

| Trigger Type | Description | Key Configuration Parameters |
|---|---|---|
| `TIME` / `SCHEDULE` | Wall-clock based scheduled runs (daily, weekly, specific dates) | `time_of_day`, `days_of_week`, `timezone` |
| `INTERVAL` | Recurring executions spaced by fixed elapsed duration | `interval_seconds` (minimum 10 seconds) |
| `CRON` | Standard 5-field UNIX cron syntax | `cron_expression`, `timezone` |
| `EVENT` | Real-time event bus matches | `event_type`, `event_filter` |
| `WATCHED_FOLDER` | Filesystem change events via Watchdog/File Monitor | `folder_path`, `file_pattern`, `recursive` |
| `DEVICE` | Android companion or external device connection/state | `device_id`, `connection_state` |
| `MANUAL` | Explicit user invocation via CLI, Desktop UI, or Tool API | None |

---

## 2. Timezone & Wall-Clock Accuracy

- Supports full IANA timezone strings (e.g. `Asia/Kolkata`, `America/New_York`, `UTC`).
- On Windows systems where system zone files may be missing, uses Python's standard `tzdata` package with an automatic fallback offset mechanism (`timezone(timedelta(hours=5, minutes=30))` for IST) so datetime calculations never crash.
- Computes `next_run` with millisecond precision and handles Daylight Saving Time (DST) transitions cleanly.

---

## 3. Event-Driven Triggers

### 3.1 Event Bus Integration
Automations subscribe to the unified `EventBus` (`core/events/bus.py`). When an event is published:
1. `EventTriggerMatcher.matches_event(automation.trigger, event)` is evaluated.
2. If `event.event_type` matches `trigger.event_type`, the trigger's `event_filter` dictionary is matched against `event.data`.
3. Event data is injected directly into the run context under the namespace `event.*`, allowing steps to reference dynamic values (e.g. `{{event.file_path}}`, `{{event.device_name}}`).

### 3.2 File Watcher Integration
- Subscribes to `FILE_CREATED`, `FILE_MODIFIED`, and `FILE_DELETED` events.
- Path prefix matching ensures that triggers only fire for files located within the designated directory tree.
- Pattern matching (`*.pdf`, `*.csv`, `*.png`) filters non-relevant filesystem events before initiating workflow execution.

### 3.3 Device Connection Triggers
- Subscribes to `DEVICE_CONNECTED`, `DEVICE_DISCONNECTED`, and `BATTERY_STATE_CHANGED`.
- Triggers cross-device sync routines immediately upon connection of registered devices (e.g., pulling phone notifications, syncing photos, or updating clipboard history).
