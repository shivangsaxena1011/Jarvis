# Expectation Engine & State Difference Detection — Phase 17

## 1. Defining Expectations
Before executing an action, the agent defines what changes *should* occur in the environment:
- **Window Changes**: `expected_state = {"window_title": "Visual Studio Code"}`
- **Text Appearance**: `expected_state = {"text_should_appear": "Test Results: 10 Passed"}`
- **Dialog Appearance**: `expected_state = {"expect_dialog": True}`
- **Element State Changes**: Enabled/disabled transitions, value updates.

---

## 2. State Difference Detection
`ExpectationEngine.compute_state_difference` compares `obs_before` and `obs_after`:
- `active_window_changed`: Detects window focus transitions.
- `new_dialog_detected`: Flags modal dialog popups (Save, Confirm, Login).
- `text_changed`: Added or removed text lines from OCR/UIA.
- `error_detected`: Scans for fatal error strings, crash dialogues, or unresponsive process notices.
- `elements_added` / `elements_removed`: Quantifies control hierarchy shifts.

---

## 3. Outcome Verification
Verification succeeds only if:
1. All declared expectations are confirmed in `obs_after`.
2. No unexpected critical errors or crashes appeared.
If expectations are unmet, the action is marked unverified with an explicit explanation (e.g. *"Expected text 'Saved' to appear, but not found"*), triggering the `ComputerRecoveryEngine`.
