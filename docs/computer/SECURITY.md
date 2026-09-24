# Computer Autonomy Security & Boundaries — Phase 17

## 1. Core Principles

### 1.1 Never Bypass Security Mechanisms
- Autonomy will **never** bypass CAPTCHA, MFA, biometric login, or password prompts.
- When an authentication challenge or CAPTCHA appears, the agent transitions to `AUTH_REQUIRED` status and yields control to the human user.

### 1.2 Resource Locking & Priority Hierarchy
Exclusive resource locks (`Desktop`, `Browser`, `Terminal`, `VSCode`, `Clipboard`) ensure background automations do not interfere with interactive user workflows:
1. `EMERGENCY_STOP` (100) — Instantly pre-empts all operations.
2. `DIRECT_USER_COMMAND` (80)
3. `USER_APPROVED_TASK` (60)
4. `INTERACTIVE_AUTOMATION` (40)
5. `SCHEDULED_AUTOMATION` (20)
6. `BACKGROUND_AUTOMATION` (10)

### 1.3 Emergency Stop & Manual Takeover
- **Emergency Stop**: Triggered by user command (*"Shivani stop"*), CLI, or REST API. Releasing locks, aborting tasks, and capturing an emergency checkpoint.
- **Manual Takeover**: When a user begins manually interacting with the computer, the agent suspends automation and re-observes the environment upon resumption to reconcile any external changes.

### 1.4 Clipboard Privacy
- Tokens, passwords, bearer credentials, and API keys are automatically detected and masked (`[REDACTED_SENSITIVE_CLIPBOARD]`).
- Sensitive clipboard contents are excluded from persistent logs and telemetry.
