# SHIVANI Real-Time Event Stream Specification

## 1. Overview
SHIVANI provides two complementary real-time streaming interfaces for desktop clients and external surfaces:
1. **WebSocket (`ws://localhost:8000/ws/events`)**: Bi-directional event stream used by the Floating HUD, Command Bar, and Desktop Dashboard.
2. **Server-Sent Events (`http://localhost:8000/events`)**: Lightweight unidirectional push stream.

---

## 2. Event Payload Schema

All streaming events adhere to the standard envelope:

```json
{
  "event": "state_changed",
  "data": {
    "state": "EXECUTING",
    "privacy_mode": false,
    "locked": false,
    "task_id": "task-7819"
  },
  "timestamp": "2026-09-24T17:45:00.123Z"
}
```

---

## 3. Core Event Types

| Event Name | Trigger | Payload Contents |
| :--- | :--- | :--- |
| `state_changed` | Assistant State Machine transition | `state`, `privacy_mode`, `locked`, `task_id` |
| `task_created` | User submits command / query | `task_id`, `query`, `status` |
| `task_step_started` | Step tool execution initiates | `task_id`, `step_id`, `tool_name`, `action` |
| `task_step_completed`| Step tool finishes execution | `task_id`, `step_id`, `tool_name`, `status`, `duration_ms` |
| `approval_required` | Sensitive or high-risk tool invoked | `request_id`, `task_id`, `tool_name`, `risk_level`, `action_summary` |
| `approval_resolved` | User approves or rejects action | `request_id`, `approved`, `resolved_by` |
| `notification_added`| New system or agent alert created | `id`, `category`, `title`, `message`, `timestamp` |
| `artifact_created` | File, report, or slide deck generated| `path`, `category`, `filename`, `size_bytes` |
| `device_connected` | Android device heartbeat received | `device_id`, `device_name`, `status` |

---

## 4. Resilience & Reconnection Protocol

- Desktop clients implement exponential backoff reconnection (`1s`, `2s`, `4s`, max `10s`).
- On successful reconnection, the client automatically requests a full state synchronization via `GET /api/status`, `GET /api/tasks`, and `GET /api/approvals`.
