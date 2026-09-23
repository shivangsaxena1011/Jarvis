# Testing & Quality Assurance — SHIVANI

SHIVANI emphasizes automated, deterministic testing across all tiers before any feature is marked `DONE`.

---

## Test Organization

- `tests/test_permissions.py`:
  - Shell command risk classifier verification (SAFE vs SENSITIVE vs CRITICAL).
  - Blocked command patterns (formatting, destructive mass deletes).
  - Path traversal attack detection.
  - Asynchronous user approval request resolution and timeouts.

- `tests/test_llm_provider.py`:
  - Provider abstraction interfaces.
  - Deterministic Mock provider plan generation.
  - Factory provider fallback on missing keys.

- `tests/test_tools.py`:
  - Tool registration and schema discovery.
  - Active window and process enumeration.
  - Desktop screen capture.
  - Filesystem read, write, and safe delete lifecycle.
  - Terminal sandboxed command execution.

- `tests/test_orchestrator.py`:
  - Hindi and Hinglish query normalization.
  - Contextual reference resolution (*"ye wala"*, *"isko"*).
  - End-to-end task execution and state machine transitions.
  - Emergency Stop abort verification.

---

## Executing Tests

Run all unit and integration tests:
```powershell
.venv\Scripts\pytest.exe -v
```
