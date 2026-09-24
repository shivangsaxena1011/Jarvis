# SHIVANI Automation Permission & Security Governance

## 1. Principles of Proactive Security

When Shivani executes automations autonomously in the background, security cannot rely on user visual oversight in the moment. Therefore:

1. **Explicit Capability Scoping**: Every automation must explicitly declare which capabilities it needs (e.g., `["email", "calendar", "notifications"]`). If an action attempts to call a tool outside its declared capabilities, the step is immediately rejected with a `Security Violation`.
2. **Path Confinement**: Automations interacting with the filesystem must declare `allowed_paths`. Any step attempting to read or write files outside these directories is blocked.
3. **No Autonomous Privilege Escalation**: An automation can never expand its own permissions or create child automations with broader permissions than itself.
4. **Human Gating for High-Risk Actions**: Any step classified as `HIGH_RISK` or `CRITICAL` (e.g., deleting directories, modifying firewall rules, sending financial transactions, or mass file modifications) automatically transitions the run into `WAITING_FOR_PERMISSION` status and alerts the user.

---

## 2. Permission Evaluation Lifecycle

In `core/automation/permissions.py`, the `AutomationPermissionEvaluator` evaluates each step:

```
Step Execution Request
       ↓
1. System Policy Check (Read-Only / Disabled)
       ↓ (Allowed)
2. Capability Match (Is tool in allowed_capabilities?)
       ↓ (Allowed)
3. Path Confinement (Are target paths within allowed_paths?)
       ↓ (Allowed)
4. Domain / Account Restriction (Are recipients whitelisted?)
       ↓ (Allowed)
5. Risk Assessment vs. max_risk_level
       ├── Risk <= max_risk_level → Auto-Approved
       └── Risk > max_risk_level OR Risk in [HIGH_RISK, CRITICAL] → Request Human Approval
```

---

## 3. Human Approval Workflow

1. The runner records an approval request in `PermissionEngine` (`security/permissions/engine.py`).
2. An event is dispatched to the Desktop HUD / System Tray / Android Companion alerting the user:
   - Automation name & step description
   - Exact tool and arguments
   - Risk justification
3. The user can **Approve** or **Reject** from the Desktop Hub, HUD toast, or CLI (`shivani automation approve <id>`).
4. Upon approval, the background runner resumes step execution. If rejected or timed out, the step transitions to `REJECTED` and the configured failure policy (`PAUSE_FOR_USER`, `STOP`, or `SKIP_STEP`) is enforced.
