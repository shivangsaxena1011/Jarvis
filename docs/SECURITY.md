# Security Architecture & Sandbox — SHIVANI

Security is a foundational pillar of SHIVANI. The agent is strictly prevented from performing arbitrary destruction or leaking confidential information.

---

## 1. Principles of Operation

- **Least Privilege**: Tools execute with the minimal required operating system permissions.
- **Explicit Authorization**: Destructive operations cannot proceed without active user consent.
- **Credential Isolation**: Secrets and keys are never hard-coded in source files or exposed to LLM context unnecessarily.
- **Zero Hallucination Tolerance**: Actions report success only when verified by ground-truth environmental checks.

---

## 2. Command Sandboxing

The `CommandValidator` inspects all terminal and shell commands prior to dispatch.

### Prohibited Command Patterns (Hard Block)
The following commands are unconditionally rejected:
- Drive formatting (`format c:`)
- Disk partitioning tools (`diskpart`, `bcdedit`)
- Mass destructive recursive deletions (`rmdir /s /q c:\`, `rm -rf /`)
- System shutdown and reboot commands (`shutdown /s`)
- Registry hive deletion (`reg delete HKLM`)
- Fork bombs (bash and batch variants)

### Dynamic Risk Elevation
Commands containing file deletions (`del`, `rm`), process terminations (`taskkill /f`, `kill`), or remote script invocations (`Invoke-Expression`, `curl | sh`) are automatically elevated to `CRITICAL` risk, requiring manual user authorization before running.

---

## 3. Path Traversal Shield

Filesystem operations validate paths against authorized workspace roots:
- Resolves symlinks and relative tokens (`..`).
- Disallows target destinations outside authorized project boundaries.

---

## 4. Secret Redaction Engine

The `AuditLogger` automatically scrubs sensitive strings using pattern matching before persisting records:
- Google Gemini API Keys (`AIza...`)
- OpenAI API Keys (`sk-...`)
- Bearer tokens, passwords, and private keys
- Key-value pairs containing keywords (`secret`, `token`, `password`, `key`)
