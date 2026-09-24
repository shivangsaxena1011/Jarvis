# Error Recovery, Adaptive Retries & Loop Detection — Phase 17

## 1. Error Classification
When an action fails or expectations are violated, `ComputerRecoveryEngine` maps the failure into typed categories:
- `ELEMENT_NOT_FOUND`: Target control could not be visually or semantically resolved.
- `UI_CHANGED`: Window, layout, or active control shifted unexpectedly.
- `TIMEOUT`: Action did not complete within the specified timeout.
- `AUTH_REQUIRED`: Password, PIN, or CAPTCHA modal appeared.
- `PERMISSION_DENIED`: Operation requires OS elevation.
- `CRASH`: Target process exited or stopped responding.
- `LOOP_DETECTED`: Repeated action or oscillating UI state.

---

## 2. Adaptive Retry Strategies
Unlike naive bots that click the same pixel coordinates 10 times in a row, Shivani escalates its strategy on retry:
1. **Retry 1**: Re-observe the desktop and search using alternative visual/OCR channels.
2. **Retry 2**: Attempt an equivalent keyboard shortcut (e.g., `Ctrl+S` instead of clicking File > Save).
3. **Retry 3**: Request interactive clarification from the user (`ASK_USER_CLARIFICATION`).

---

## 3. Automation Loop Detection
`LoopDetector` tracks recent action and state signatures:
- **Repetition Check**: Identical action repeated $\ge 3$ consecutive times triggers `LOOP_DETECTED`.
- **Oscillation Check**: Alternating states ($A \to B \to A \to B$) triggers `LOOP_DETECTED`.
- When triggered, operations pause safely to prevent runaway cursor movements or accidental inputs.
