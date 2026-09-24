# Closed-Loop Action Engine — Phase 17

## 1. Action Model (`ComputerAction`)
Every physical or synthetic desktop operation is represented by a structured `ComputerAction`:

```python
class ComputerAction(BaseModel):
    id: str
    action_type: ActionType       # CLICK, DOUBLE_CLICK, RIGHT_CLICK, TYPE, HOTKEY, SCROLL, DRAG, OPEN, CLOSE, etc.
    target: Optional[str]         # Semantic query, e.g. "Save button"
    parameters: Dict[str, Any]    # Action parameters (x, y, text, keys, etc.)
    expected_state: Dict[str, Any]# Expected post-conditions
    risk: str                     # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float             # Target resolution confidence
    timeout_seconds: float        # Execution timeout
    verification: Dict[str, Any]  # Verification rules
    rollback: Optional[Dict]      # Compensating rollback action
```

---

## 2. Closed-Loop Execution Lifecycle

1. **Pre-Observation**: Captures baseline desktop observation (`obs_before`).
2. **Grounding & Validation**: Resolves target semantic query to coordinates or control handles; verifies confidence exceeds threshold.
3. **Dispatch**: Sends input via `OperatingSystemAdapter` (keyboard-first, mouse fallback).
4. **Settle Window**: Waits for OS event queues and animations to settle.
5. **Post-Observation**: Captures state after action (`obs_after`).
6. **Expectation Verification**: Computes `StateDifference` and validates that post-conditions are satisfied.
7. **Loop Tracking**: Feeds action and state fingerprints into the `LoopDetector`.
