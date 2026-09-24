# SHIVANI Background Worker & Process Lifecycle

## 1. Role of the Background Worker

The `AutomationWorker` (`core/automation/worker.py`) is the persistent daemon responsible for autonomous task execution when Shivani is running in the background.

```
+-------------------------------------------------------------+
|                     AUTOMATION WORKER                       |
|                                                             |
|   ┌─────────────────────────────────────────────────────┐   |
|   │ 1. Sleep / Wake Detection & Elapsed Drift Check     │   |
|   └──────────────────────────┬──────────────────────────┘   |
|                              v                              |
|   ┌─────────────────────────────────────────────────────┐   |
|   │ 2. Battery & Resource Monitor (Defer if < 20%)      │   |
|   └──────────────────────────┬──────────────────────────┘   |
|                              v                              |
|   ┌─────────────────────────────────────────────────────┐   |
|   │ 3. Priority Yield (Pause if User Interactive Task)  │   |
|   └──────────────────────────┬──────────────────────────┘   |
|                              v                              |
|   ┌─────────────────────────────────────────────────────┐   |
|   │ 4. Due Automations Query & Execution Dispatch       │   |
|   └─────────────────────────────────────────────────────┘   |
+-------------------------------------------------------------+
```

---

## 2. Key Worker Subsystems

### 2.1 Sleep / Wake Detection & Reconciliation
- The worker maintains a steady loop heartbeat (default: 5s).
- If the difference between current wall time and previous heartbeat exceeds `2 * poll_interval + 5s`, the system has woken from sleep or hibernation.
- **Catch-Up Reconciliation**:
  - `RUN_ONCE`: Runs any missed automations exactly once immediately upon waking.
  - `SKIP`: Advances the `next_run` timestamp to the next future scheduled occurrence without backfilling missed runs.
  - `RUN_ALL`: Queues every missed occurrence in chronological sequence.

### 2.2 Battery & Resource Awareness
- Uses `psutil.sensors_battery()` to check laptop power state.
- If battery level is below 20% and AC power is disconnected, non-critical background automations are deferred to preserve power.
- Deferral notifications are recorded in automation history so the user knows why a run was postponed.

### 2.3 Priority Yielding
- The worker queries active user sessions.
- If the user is currently engaged in high-intensity interactive tasks (voice conversation, interactive computer-use agent), background automations yield execution priority until the interactive session completes.
