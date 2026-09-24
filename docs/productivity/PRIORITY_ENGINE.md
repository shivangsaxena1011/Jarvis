# Multi-Factor Priority Engine & Transparency

## 1. Multi-Factor Formula
The `PriorityEngine` ranks tasks along a deterministic, multi-dimensional scale from `0.0` to `100.0`.

$$\text{Score} = \min(100.0, W_{\text{base}} + W_{\text{deadline}} + W_{\text{dependency}} + W_{\text{project}} + W_{\text{effort}})$$

### Factors & Weights

1. **Base Priority Weight ($W_{\text{base}}$)**:
   - `CRITICAL`: 40 points
   - `HIGH`: 30 points
   - `MEDIUM`: 20 points
   - `LOW`: 10 points

2. **Deadline Proximity ($W_{\text{deadline}}$)**:
   - Overdue: +35 points
   - Due Today: +25 points
   - Due Tomorrow: +15 points
   - Due This Week (2-7 days): +8 points

3. **Dependency Impact ($W_{\text{dependency}}$)**:
   - Unblocks downstream tasks: $+5$ points per unblocked task (max 20 points).
   - If blocked by another task: Score scaled down by $0.3\times$ to avoid recommending actionable work when prerequisites are missing.

4. **Project Alignment ($W_{\text{project}}$)**:
   - Linked to a High/Critical Priority Project: +10 points.

5. **Quick-Win Effort Factor ($W_{\text{effort}}$)**:
   - High priority tasks under 30 minutes receive a $+5$ point quick-win boost.

---

## 2. Transparent Justifications (`why_surfaced`)
Every calculation yields a clear textual justification:
```json
{
  "score": 85.0,
  "reasons": [
    "Base priority is CRITICAL",
    "Task is due today",
    "Unblocks 2 downstream tasks",
    "Belongs to active high-priority project 'Alpha'"
  ]
}
```
This ensures the user is never subjected to arbitrary black-box sorting.
