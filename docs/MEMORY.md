# Memory Hierarchy — SHIVANI

SHIVANI implements a multi-tier memory architecture to sustain long-running state and personal user preferences without leaking credentials.

---

## Memory Tiers

```
┌────────────────────────────────────────────────────────┐
│                   Short-Term Memory                    │
│   Active session context, focused window, recent query │
├────────────────────────────────────────────────────────┤
│                   Long-Term Memory                     │
│  User preferences, default apps, authorized workspaces │
├────────────────────────────────────────────────────────┤
│                    Semantic Memory                     │
│  Vector embeddings for projects, notes, and codebase   │
└────────────────────────────────────────────────────────┘
```

---

## 1. Short-Term Memory
- Managed by `SessionContext`.
- Retains active foreground window title, current directory, focused file, and recent user queries for deictic reference resolution (*"ye wala"*, *"isko"*).
- Cleared upon task completion or agent restart.

---

## 2. Long-Term Memory
- Stored as structured JSON / SQLite records.
- Records persistent user settings (e.g. preferred browser, editor preference, music preferences).

---

## 3. Privacy & Sanitization Guardrails
- **Strictly Prohibited from Memory**: Passwords, OTP codes, API secret tokens, recovery keys, credit card details.
- Secrets are detected by regex patterns and intercepted before any memory persistence layer.
