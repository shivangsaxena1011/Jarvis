# SHIVANI Security Model & Architecture

## 1. Principles of Operation
SHIVANI operates under a zero-trust, privacy-first, and fail-closed security architecture designed for personal autonomous computer use.
The system guarantees that:
1. **No Destructive Action Unconfirmed**: High-risk system actions (disk formats, command injections, system deletions) are blocked by default or require explicit user confirmation.
2. **Zero Plaintext Credentials on Disk**: Sensitive secrets, access tokens, and API keys are protected using native Windows DPAPI (`CryptProtectData`) with hardware-bound keys.
3. **Fail-Closed Execution**: If any security component, policy check, or boundary validator encounters an error or ambiguous state, execution immediately halts and authorization is denied.
4. **Scoped Permissions & Timeouts**: Approvals are bound strictly by scope (`ONE_ACTION`, `TASK_SCOPE`, `WORKFLOW_SCOPE`, `TIME_LIMITED`) preventing lingering open privileges.
5. **Authoritative Emergency Kill-Switch**: The `EmergencyController` provides an instantaneous, top-priority halt across all threads, subprocesses, subagents, and mesh devices.

---

## 2. 5-Tier Risk Classification
All actions and tools are classified into 5 strict risk levels:
- **SAFE**: Read-only, deterministic queries with no side-effects (e.g. system time, file existence check, calculator, help query).
- **LOW_RISK**: Local operations with minimal side-effects (e.g. directory listing, local status queries).
- **SENSITIVE**: Read operations of personal user data, web navigation, creating new workspace files.
- **HIGH_RISK**: Modifying system files, installing packages, sending emails, external API write actions.
- **CRITICAL**: Executing arbitrary terminal commands, deleting files/directories, credential manipulation, system reboots.

---

## 3. Scoped Approval Engine
When an action requires confirmation, an `ApprovalRequest` is created. Approvals can be granted with explicit boundaries:
- `ApprovalScope.ONE_ACTION`: Valid for exactly one invocation. Automatically discarded immediately upon use.
- `ApprovalScope.TASK_SCOPE`: Valid only for the lifetime of the requesting `task_id`. Revoked upon task completion or failure.
- `ApprovalScope.WORKFLOW_SCOPE`: Valid across coordinated workflow steps, expiring upon workflow termination.
- `ApprovalScope.TIME_LIMITED`: Hard expiration timestamp. Invocations past the deadline are rejected.

---

## 4. Path Traversal & Filesystem Containment
All file operations are validated via `PathValidator.validate_within_boundary()`:
- Paths are fully resolved to canonical absolute paths (`Path.resolve()`).
- Path traversal sequences (`..`, hidden dotfiles, NTFS alternate data streams) are checked.
- Sensitive operating system directories (`%SYSTEMROOT%`, `System32`, `SAM`, `drivers\etc\hosts`) are forbidden.
- Backups and restorations enforce strict zip-slip protection preventing directory escape during decompression.
