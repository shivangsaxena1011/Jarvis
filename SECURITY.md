# SHIVANI Security Policy & Threat Model

## 1. Overview & Security Philosophy

**SHIVANI** is an autonomous personal AI computer-use agent designed with deep operating system integration across Windows desktop applications, web browsers, local filesystems, external APIs, and paired mobile companion devices.

Because SHIVANI can observe and act upon user environments, security is not an afterthought or an external wrapper—it is built into every layer under the strict operational discipline:
$$\text{OBSERVE} \longrightarrow \text{PLAN} \longrightarrow \text{ACT} \longrightarrow \text{VERIFY}$$

---

## 2. Threat Model & Defensive Architecture

```
[ External Untrusted Data ] (Web, Email, Repositories, PDFs)
            │
            ▼
[ Prompt Injection Classifier ] ──► (Flag & Sanitize / Neutralize Boundary Escapes)
            │
            ▼
     [ Planning Engine ]
            │
            ▼
      [ Policy Engine ] ──► 5-Tier Risk Evaluation (SAFE to CRITICAL)
            │                User Confirmation & Approval Flow
            ▼
    [ Command Validator ] ──► Strict Blocklist (format, rm -rf, fork bombs)
            │
            ▼
     [ Path Validator ] ──► Directory Traversal & Symlink Boundary Check
            │
            ▼
     [ Process Sandbox ] ──► Stripped API Keys, Execution Timeout, Memory Limits
            │
            ▼
  [ Hardware DPAPI Vault ] ──► Zero Plaintext Credentials on Disk
            │
            ▼
   [ Structured Audit Log ] ──► Redacted JSONL Event Stream & Size Rotation
```

### A. Prompt Injection Defense
- **Content Classification**: All external content ingested from websites, emails, GitHub issues, and documents is classified as `EXTERNAL_DATA` or `UNTRUSTED_INSTRUCTION`.
- **Structural Demarcation**: Untrusted inputs are wrapped inside explicit immutable boundaries:
  `<<<UNTRUSTED_EXTERNAL_DATA source="source_name">>> ... <<<END_UNTRUSTED_EXTERNAL_DATA>>>`
- **Jailbreak Detection**: Active regex and heuristic classifiers flag instruction overrides ("ignore prior instructions", "developer override mode", "system prompt reset", DAN attacks) and neutralize embedded boundary tags.

### B. Command Execution & Subprocess Sandboxing
- **Command Risk Classification**:
  - `SAFE`: Non-destructive inspection (`dir`, `git status`, `echo`, `python --version`).
  - `WARNING`: Active builds and modifications (`pip install`, `git commit`, `node`).
  - `DANGEROUS`: Process termination, file deletion (`del`, `rmdir`, `taskkill`).
  - `BLOCKED`: Absolute destructive actions strictly barred from execution (`format C:`, `rmdir /s /q C:\`, `rm -rf /`, `diskpart`, `bcdedit`, fork bombs).
- **Environment Sanitization**: `ProcessSandbox` scrubs critical secrets (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `GITHUB_TOKEN`, `SHIVANI_DEVICE_SECRET`) from child process environments before spawning.
- **Resource Constraints**: Hard execution timeouts (default 30s) and stdout/stderr output caps prevent denial-of-service via infinite output streams or runaway loops.

### C. Filesystem Protection & Path Traversal Prevention
- `PathValidator` ensures every file read, write, and delete operation resolves strictly within authorized workspace roots.
- Prevents directory traversal sequences (`..`), relative link bypasses, and symlink/junction escapes.
- System-critical roots (`C:\Windows`, `C:\Program Files`, `~/.ssh`, `~/.aws`, `~/.gnupg`, `/etc`) are strictly write-protected.

### D. Credential & Secret Management
- **Hardware-Backed Encryption**: Credentials, access tokens, and passwords are encrypted using **Windows DPAPI** (`CryptProtectData` and `CryptUnprotectData`), bound to the logged-in Windows user account and machine hardware key.
- **Zero Plaintext Storage**: Plaintext secrets are never stored on disk, never serialized into database records, and never written into checkpoints.
- **Redaction Engine**: The audit logging subsystem automatically scrubs detected API keys, passwords, and tokens, replacing them with `[REDACTED_SECRET]`.

### E. Mobile Device Bridge & Replay Protection
- **HMAC-SHA256 Signatures**: Every payload exchanged between laptop SHIVANI and the Android companion app is digitally signed using a pre-shared cryptographic secret.
- **Anti-Replay Guards**: Nonces and UTC timestamps are tracked; messages outside a 60-second clock skew window or containing previously observed nonces are rejected.

### F. Operational Modes & Emergency Stop
- **Safe Mode (`SHIVANI_SAFE_MODE=1`)**: Restricts system actions strictly to `SAFE` and `LOW_RISK` tiers; completely bars shell execution and disk mutations.
- **Demo Mode (`SHIVANI_DEMO_MODE=1`)**: Mocks external operations with zero live mutations, outputting safe previews.
- **Global Emergency Stop**: Immediate abort mechanism that cancels all running async tasks and triggers registered cleanup handlers across browser sessions, companion bridge sockets, and input hooks.

---

## 3. Reporting a Security Vulnerability

If you discover a potential security vulnerability within SHIVANI, please do **NOT** open a public issue.

Send a detailed report to:
- **Email**: `security@project-shivani.internal`
- Please include:
  1. Description of the vulnerability and attack vector
  2. Proof of concept (PoC) or reproducible steps
  3. Potential impact on host systems or user data

We acknowledge receipt within 24 hours and provide patch updates within 72 hours for critical vulnerabilities.
