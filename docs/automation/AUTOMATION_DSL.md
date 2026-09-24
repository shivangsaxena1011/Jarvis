# SHIVANI Automation DSL & Natural Language Compiler

## 1. Overview
The Automation Domain-Specific Language (DSL) allows users to define automations through:
1. **JSON / YAML schema**: Typed, structured, schema-validated representation.
2. **Natural Language Prompts**: Automatically parsed and compiled into valid DSL specifications by `AutomationDSLCompiler`.
3. **Conversational Editing**: Modifies specific properties of an existing automation in place using natural language commands.

---

## 2. DSL Schema Specification

Every automation conforms to the `Automation` model in `core/automation/models.py`.

```json
{
  "id": "auto_morning_brief",
  "name": "Morning Briefing",
  "description": "Summarizes calendar, weather, and emails every morning at 08:00 AM",
  "trigger": {
    "type": "schedule",
    "schedule": {
      "time_of_day": "08:00",
      "days_of_week": [0, 1, 2, 3, 4],
      "timezone": "Asia/Kolkata"
    }
  },
  "conditions": {
    "operator": "AND",
    "predicates": [
      {
        "field": "network.online",
        "operator": "equals",
        "value": true
      }
    ]
  },
  "steps": [
    {
      "step_id": "fetch_calendar",
      "name": "Get Today's Events",
      "tool": "calendar.list_events",
      "input_template": { "time_min": "today_start", "time_max": "today_end" },
      "risk_level": "safe"
    },
    {
      "step_id": "summarize",
      "name": "Synthesize Brief",
      "tool": "llm.synthesize",
      "input_template": { "context": "{{step_fetch_calendar_output}}" },
      "risk_level": "safe"
    },
    {
      "step_id": "notify",
      "name": "Show HUD Notification",
      "tool": "notification.display",
      "input_template": { "title": "Good Morning!", "body": "{{step_summarize_output}}" },
      "risk_level": "safe"
    }
  ],
  "permissions": {
    "allowed_capabilities": ["calendar", "llm", "notifications"],
    "allowed_paths": [],
    "max_risk_level": "safe",
    "requires_user_present": false
  },
  "failure_policy": "retry",
  "max_retries": 2,
  "notification_policy": {
    "on_success": false,
    "on_failure": true,
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00"
  }
}
```

---

## 3. Natural Language Compiler

The natural language compiler (`AutomationDSLCompiler.compile_prompt_to_automation`) translates user instructions into executable automation definitions:

### Example Prompts Handled:
1. *"Every morning at 8:30 AM, fetch my unread emails and summarize them in a notification."*
   - Trigger: Time trigger at `08:30` daily.
   - Steps: `email.fetch` -> `llm.summarize` -> `notification.display`.
   - Capabilities: `["email", "notifications", "llm"]`.

2. *"Whenever a file is added to C:/Downloads, scan it and move it to C:/Documents/Scanned."*
   - Trigger: Event trigger (`EventType.FILE_CREATED`) with path prefix `C:/Downloads`.
   - Steps: `file.scan` -> `file.move`.
   - Capabilities: `["file_system"]`.

3. *"Every 30 minutes, check github for open PRs."*
   - Trigger: Interval trigger (`interval_seconds: 1800`).
   - Steps: `github.list_prs`.

---

## 4. Conversational Editing

The DSL compiler supports modifying existing routines through natural language directives:
- *"Change the time to 9:00 AM."* -> Updates `trigger.schedule.time_of_day`.
- *"Add a step to notify my phone."* -> Appends a new push notification step.
- *"Disable it during weekends."* -> Sets `days_of_week` to `[0, 1, 2, 3, 4]`.
- *"Set max retries to 3."* -> Updates `max_retries`.

---

## 5. Dry-Run Sandbox Simulation

Before activating an automation, users can preview and simulate execution:
- Replaces real tool actions with safe mock dispatches.
- Simulates step output propagation and template resolution.
- Validates permissions against the user's current security policies without mutating system state.
