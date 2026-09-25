# SHIVANI Threat Model & Attack Surface Analysis

## 1. Threat Actors & Vectors
| Actor | Motivation | Attack Vector | Mitigation in SHIVANI |
|---|---|---|---|
| **Malicious Web Pages / Third Parties** | Data exfiltration, drive-by prompt injection | Ingested HTML, hidden markdown comments, zero-width spaces | `PromptInjectionClassifier` fences all external inputs in `<UNTRUSTED_EXTERNAL_DATA>` tags. Active tags are stripped. |
| **Untrusted Repository / Document** | Local code execution, privilege escalation | Poisoned README, malicious script targets | `CommandValidator` and `ProcessSandbox` block destructive command tokens (`rm -rf`, `format`, `del /s /q`). |
| **Compromised Subagent / Hallucinating Model** | Runaway operations, endless loops | Repetitive actions, repeated errors, excessive steps | `TaskWatchdog` flags stuck tasks and halts them into `BLOCKED`. `EmergencyController` provides global abort. |
| **Local Disk Snooper** | Secret theft, API token harvesting | Reading unencrypted config files on disk | Windows DPAPI encrypts all secrets in `vault.enc`. Zero plaintext secret persistence. |
| **Mesh Man-in-the-Middle** | Command injection via mobile companion | Replayed or forged network packets | HMAC-SHA256 signatures, timestamps, unique nonce verification, and 6-digit cryptographic pairing. |

---

## 2. STRIDE Assessment Matrix

### Spoofing
- **Threat**: Attacker spoofing peer mesh device commands.
- **Defense**: Peer authentication using shared secret derived during initial out-of-band PIN exchange; packets signed with HMAC-SHA256 and single-use nonces.

### Tampering
- **Threat**: Tampering with persistent memory or backups.
- **Defense**: SHA-256 cryptographic checksums on backup manifests (`.manifest.json`); zip-slip path validation on restoration.

### Repudiation
- **Threat**: Autonomous actions executed without audit trail.
- **Defense**: Unified audit logging (`observability/audit_logger.py`) records all tool invocations, arguments, user approvals, and timestamps.

### Information Disclosure
- **Threat**: Cloud model leaking personal documents or credentials.
- **Defense**: Hybrid routing (`OfflineMode`, `PrivacyLevel.CRITICAL`) directs sensitive queries exclusively to local models (e.g. Ollama `llama3.1:8b`) or rejects cloud routing.

### Denial of Service
- **Threat**: Runaway agent consuming 100% CPU or exhausting API limits.
- **Defense**: `TaskWatchdog` enforces step limits (default: 25 steps), timeout ceilings (90s without progress), and loop detection.

### Elevation of Privilege
- **Threat**: Agent executing administrative or destructive Windows shell commands.
- **Defense**: Hardcoded blocked command catalog in `CommandValidator` unconditionally blocks `bcdedit`, `format`, `diskpart`, `rmdir /s /q`, and registry alterations.
