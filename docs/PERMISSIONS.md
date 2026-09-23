# Permission Engine & Approval Workflow — SHIVANI

The Permission Engine mediates every tool request in the SHIVANI runtime.

---

## 1. Risk Classification Tiers

```
┌────────────────────────────────────────────────────────┐
│                        CRITICAL                        │
│   Mass deletes, disk formatting, process kills, etc.   │
│            STRICT: ALWAYS REQUIRES APPROVAL            │
├────────────────────────────────────────────────────────┤
│                       SENSITIVE                        │
│   File writes, git commits, builds, network uploads    │
│           STRICT & STANDARD: REQUIRES APPROVAL         │
├────────────────────────────────────────────────────────┤
│                          SAFE                          │
│     Screenshots, active window, list files, read       │
│               AUTO-APPROVED ACROSS MODES               │
└────────────────────────────────────────────────────────┘
```

---

## 2. Policy Modes

Configured via `SECURITY_POLICY` in `.env`:
- **`strict`** (Default): Requires explicit user approval for all `SENSITIVE` and `CRITICAL` operations.
- **`standard`**: Automatically executes `SENSITIVE` actions while notifying the user; strictly requires explicit approval for `CRITICAL` operations.
- **`lenient`**: Automated testing mode; prompts only on `CRITICAL` operations.
- **`test`**: Automated headless test harness mode with mock approvals.

---

## 3. Approval Request Lifecycle

```
[Tool Invocation]
       │
       ▼
[Risk Evaluation]
       │
       ├── SAFE ───────────────────────────────► [Execute Immediately]
       │
       └── SENSITIVE or CRITICAL
               │
               ▼
       [Create ApprovalRequest]
               │
               ├──► [Push to Desktop UI Modal / Voice Prompt]
               │
               ▼
       [Wait for Resolution (120s timeout)]
               │
               ├── Approved ───────────────────► [Execute Tool]
               ├── Rejected ───────────────────► [Halt Task with Error]
               └── Expired (Timeout) ──────────► [Abort Operation Safely]
```

---

## 4. Approval Interface

When an approval request is triggered:
- The Desktop Web Dashboard renders an amber pulsating Approval Card detailing:
  - Task ID and Query
  - Tool Name and Risk Tier
  - Target Path or Command
  - Description of intended side effect
- Interactive **[Approve]** and **[Reject]** buttons resolve the pending future.
- In voice-enabled mode, the assistant inquires: *"Shivani: I need your confirmation before deleting temp_to_delete.txt. Should I proceed?"*
