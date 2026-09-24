# SHIVANI Automation Failure Handling & Self-Recovery

## 1. Failure Policies

Every automation step and parent automation configures a `FailurePolicy` (`core/automation/models.py`):

| Policy | Behavior |
|---|---|
| `STOP` | Immediately terminates the workflow run. Marks run status as `FAILED`. |
| `RETRY` | Retries the step using exponential backoff up to `max_retries` times. |
| `SKIP_STEP` | Logs warning, marks step as `SKIPPED`, and continues to the next step. |
| `FALLBACK` | Executes an alternate pre-configured recovery step or tool. |
| `PAUSE_FOR_USER` | Suspends workflow in `PAUSED` state and requests user intervention. |

---

## 2. Exponential Backoff & Jitter

When a step fails under the `RETRY` policy:
- Attempt 1: Immediate retry or 1s delay
- Attempt 2: 2s delay
- Attempt 3: 4s delay
- Attempt 4: 8s delay

Formula: `delay = min(max_delay, initial_delay * (2 ** (attempt - 1)))`

If all retry attempts are exhausted, the step transitions to `FAILED` and triggers the parent automation's failure policy.

---

## 3. Idempotency Guards

Duplicate execution can cause severe real-world harm (e.g. duplicate payment, duplicate customer email, duplicate git tag).
Shivani implements a two-tier idempotency system:

1. **Explicit Key**: If the step specifies an `idempotency_key` (e.g. `send_invoice_inv1234`), the key is checked in the SQLite table `idempotency_records`. If already recorded, the step is immediately skipped with status `SKIPPED_DUPLICATE`.
2. **Deterministic Input Hash**: If no explicit key is provided, an automatic SHA-256 fingerprint of the automation ID, step ID, and normalized argument dictionary is generated:
   `hash = sha256(automation_id + step_id + json_dumps(args))`

---

## 4. Run State Auditing & Rollbacks

- Every run records exact start/end timestamps, step-by-step inputs, outputs, errors, and warnings.
- Run records are persisted immediately to disk, ensuring that unexpected process termination (crash or power loss) preserves the exact failure state for diagnosis and resume.
