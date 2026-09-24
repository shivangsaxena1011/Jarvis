# SHIVANI Human-in-the-Loop Approval UX & Risk Classification

## 1. 5-Tier Risk Classification Taxonomy

Security in SHIVANI is proactive and contextual. Every tool invocation evaluates its assigned risk level:

| Risk Tier | Examples | Default Policy Action |
| :--- | :--- | :--- |
| **SAFE** | Read-only queries, web search, reading public notes, viewing memory. | Auto-approved silently. |
| **LOW_RISK** | Creating scratch notes, taking local screenshots, playing local audio. | Auto-approved with audit logging. |
| **SENSITIVE** | Accessing user contacts, sending internal emails, modifying non-critical configs. | Prompts user confirmation if strict policy. |
| **HIGH_RISK** | Executing terminal commands, writing to source files, updating databases. | Mandatory user confirmation dialog. |
| **CRITICAL** | File deletions, executing root/admin scripts, external social publishing, device resets. | Mandatory explicit modal with warning badge. |

---

## 2. Approval Request Modal Design

When a tool requires human approval, execution pauses and renders a high-visibility modal card:

```
+-------------------------------------------------------------------------+
| [⚠️ APPROVAL REQUIRED] High-Risk System Action                          |
|                                                                         |
| Tool:      terminal_execute                                             |
| Target:    C:/Users/Project/Jarvis/cache                                |
| Action:    Delete build cache directory                                 |
| Arguments: {"command": "rm -rf cache"}                                  |
| Risk:      [HIGH_RISK]                                                  |
| Reversibility: [NON-REVERSIBLE ACTION]                                  |
|                                                                         |
| The assistant is requesting permission to execute the shell command     |
| shown above. This operation cannot be automatically undone.             |
|                                                                         |
| [ Deny Action ]         [ Approve Once ]         [ Approve for Task ]   |
+-------------------------------------------------------------------------+
```

---

## 3. Resolution Scopes

- **Approve Once**: Grants permission for this single invocation only. Subsequent calls will re-prompt.
- **Approve for Task**: Adds a session pre-approval token (`{task_id}:{tool_name}`) to the `PermissionEngine`, allowing batch steps within this specific workflow without interrupting the user.
- **Deny Action**: Immediately rejects the approval request, returning an authorization error to the planner so it can abort or replan via an alternate safe path.
