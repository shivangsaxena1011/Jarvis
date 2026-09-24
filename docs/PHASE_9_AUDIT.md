# SHIVANI — Comprehensive Phase 9 Architecture & Security Audit

**Date**: September 24, 2026  
**Auditor**: Senior AI Systems Architect & Cybersecurity Engineer  
**Scope**: Complete SHIVANI Project Repository (Phases 1 through 8 Baseline)  
**Commit**: `d0af271`

---

## 1. Current Architecture

SHIVANI is architected as a modular, privacy-first, voice-enabled autonomous computer-use operating layer on Windows 11 with companion Android bridge capabilities.

The core runtime follows an event-driven, decoupled pipeline:
```
User (Voice / CLI / API / Dashboard)
  ↓
Wake Word ("Shivani") & Local Audio Capture (openWakeWord + PyAudio)
  ↓
Speech-to-Text (Local Faster-Whisper / Cloud Fallback)
  ↓
Conversational Normalizer & Context Builder (Hinglish/Hindi + History + Desktop State + Memory)
  ↓
Orchestrator & Task Decomposer (Directed Acyclic Graph across sub-agents)
  ↓
LLM Provider Abstraction (Gemini, Local/Ollama, Mock)
  ↓
Task Planner (OBSERVE → PLAN → PERMISSION → ACT → VERIFY)
  ↓
Security & Permission Engine (Dynamic Policies + Risk Classifier + Audit Logger)
  ↓
Concurrence & Resource Manager (File, Repo, Device, Browser Locks)
  ↓
Specialized Sub-Agents & Tool Registry (151 Registered Tools across 7 Agents)
  ├─ ComputerAgent (Windows Desktop, UI Context, Win32/PyAutoGUI)
  ├─ BrowserAgent (Playwright, Tab/DOM Extraction, Navigation)
  ├─ CodingAgent (Project Analysis, AST/Symbol, Testing, Git)
  ├─ ResearchAgent (Multi-source Web Synthesis, Citations, Reports)
  ├─ PresentationAgent (python-pptx Pitch Decks, Theming)
  ├─ DocumentationAgent (README, API & Architecture Docs)
  └─ PhoneAgent (Secure Device Bridge, Mock/ADB, Mobile UI)
  ↓
Execution Verification & Recovery Checkpoint Engine
  ↓
Persistent Scoped Memory (SQLite, Secret Sanitization, TTL Purging)
  ↓
TTS Engine & Notification Center (pyttsx3/Edge-TTS, Real-time Alerts)
```

---

## 2. Implemented Features

### Phase 1: Foundation & Core Runtime
- Configuration management with Pydantic settings.
- LLM Provider Abstraction (`LLMProvider`, `GeminiProvider`, `MockProvider`, factory).
- Tool Registry with argument schemas, risk levels, and timeout controls.
- Central Orchestrator, Task Planner, and Task Executor.
- EventBus with asynchronous event emissions and audit logging.
- Emergency Stop controller for task aborts.
- FastAPI REST backend + WebSocket live event streams.

### Phase 2: Voice, Wake Word & Speech
- Wake word detector ("Shivani") with sensitivity and cooldown.
- Audio pipeline with microphone capture, energy thresholding, and silence trimming.
- Dual STT (Faster-Whisper local + cloud fallback) with confidence scoring.
- Dual TTS (pyttsx3 offline + Edge-TTS high-quality).
- Hinglish & Hindi normalizer with deictic reference resolution.

### Phase 3: Computer Use & Windows Desktop Control
- Operating System adapter layer (`WindowsAdapter`, `MockOSAdapter`).
- Application lifecycle management (open, close, focus, list).
- Window management (minimize, maximize, restore, close, active window inspection).
- Precise input automation (mouse move, click, drag, scroll, keyboard type, hotkeys).
- Clipboard operations (read, write, clear).
- Screen observation & screenshot capture with coordinate bounding.

### Phase 4: Universal Browser Agent
- Playwright-backed headless/headful browser automation.
- DOM exploration without arbitrary coordinate guessing (role, text, CSS, XPath selectors).
- Tab management (new tab, switch, close, list).
- Data extraction (full text, links, structured tables, summaries).
- File upload/download automation.

### Phase 5: Productivity Integrations & Cross-App Workflows
- YouTube automation (search, direct play, pause, resume, progress inspection).
- Gmail triage (search, list unread, summarize threads, cleanup proposal, delete).
- LinkedIn automation (feed reading, post generation, draft preparation, human approval gates).
- GitHub repository inspector (structure, file reading, issues, runnable detection).
- Autonomous research service (search, summarize, markdown report bundle).
- Multi-step declarative WorkflowEngine with checkpoints and state machine.

### Phase 6: Professional Agents
- AI Software Engineer (`CodingAgent`): inspect projects, search code, patch files, run pytest/npm builds, analyze stack traces, Git diff/commit/push.
- Research Assistant (`ResearchAgent`): authoritative literature gathering, synthesis, and structured reporting.
- Presentation Builder (`PresentationAgent`): PowerPoint generation with custom color palettes, slide structures, and pitch decks.
- Documentation Agent (`DocumentationAgent`): automated README and architectural docs generation.

### Phase 7: Android Phone Agent & Secure Device Bridge
- Secure Device Bridge with HMAC-SHA256 handshake and token-based message signing.
- Android Phone Agent (`PhoneAgent`): launch apps, open settings, navigation (Home, Back), UI tree inspection, gestures (Tap, Swipe, Long Press), photos, notifications.
- Cross-device workflow recipes (e.g. transfer photo from phone to PC, inspect code, draft post).
- Kotlin Jetpack Compose companion mobile app (`apps/mobile`).

### Phase 8: Memory, Multi-Agent Orchestration & Proactive Scheduling
- Persistent SQLite-backed memory store with schema versioning.
- Scoped memory isolation (`GLOBAL`, `PROJECT`, `TASK`, `DEVICE`, `SESSION`).
- Sub-memory modules: Preferences with conflict overrides, Short-term conversation history, Episodic completed tasks, Semantic domain facts, Task checkpoints.
- Strict `SecretRedactor` automatically scrubbing API keys, tokens, and passwords (`[REDACTED_SECRET]`).
- TaskDecomposer: Directed Acyclic Graph (DAG) generation across sub-agents with dependency progression.
- ResourceManager: Fine-grained concurrency locks for files, repositories, devices, and browser sessions.
- Notification Center: Prioritized alerting (`INFO`, `SUCCESS`, `WARNING`, `ACTION_REQUIRED`, `ERROR`).
- SchedulerService: Periodic/interval workflows with SHA-256 state idempotency guards.
- Total Registered Tools: Exactly 151 tools.

---

## 3. Incomplete Features & Architectural Gaps

1. **Dedicated Security Subsystem**:
   - `security/` currently contains only `permissions/engine.py`, `audit/logger.py`, and `sandbox/command_validator.py`.
   - Missing dedicated modules: `security/permissions.py` (5-tier risk taxonomy), `security/policy_engine.py`, `security/risk_classifier.py`, `security/secret_manager.py` (DPAPI/Windows Credential Manager integration), `security/secure_storage.py`, `security/session_security.py`, `security/device_security.py`, `security/command_validation.py`, `security/sandbox.py`, `security/security_events.py`, and `security/prompt_injection.py`.

2. **Prompt Injection Defenses**:
   - Current web text extraction and email reading inject content directly into task context without untrusted data tagging or prompt injection classification (`TRUSTED_INSTRUCTION`, `USER_CONTENT`, `EXTERNAL_DATA`, `UNTRUSTED_INSTRUCTION`, `POTENTIAL_PROMPT_INJECTION`).

3. **Reversible Operations & Rollback Engine**:
   - Destructive operations (file edits, deletes) currently do not have a dedicated `recovery/` subsystem (`checkpoint_manager.py`, `rollback_manager.py`, `transaction_manager.py`, `backup_manager.py`, `recovery_engine.py`) to create pre-execution snapshots and rollback upon failure.

4. **Resource Quotas & Execution Budgets**:
   - Execution limits (max task runtime, max tool calls, max retries, max shell execution duration, max browser tabs) are not unified in a configurable central limit registry.

5. **Local AI / Offline Fallback Mode**:
   - No direct Ollama or local OpenAI-compatible inference provider is configured for graceful offline fallback when internet connectivity drops.

6. **Observability & Local Telemetry**:
   - Need dedicated `observability/` subsystem (`metrics.py`, `tracing.py`, `health.py`, `diagnostics.py`, `performance.py`) tracking task durations, latencies, and tool performance.

7. **Packaging & Distribution**:
   - Missing Windows installer configuration (`Shivani-Setup.exe`), portable distribution archive (`Shivani-Portable.zip`), `%APPDATA%\Shivani\` directory migration, and uninstall scripts.

8. **CLI Suite**:
   - Missing `shivani start`, `shivani stop`, `shivani status`, `shivani doctor --full`, `shivani logs`, `shivani test`, `shivani config`, `shivani task "<query>"`.

---

## 4. Known Bugs & Code Smells Identified

1. **Unclosed Process Pipe Warnings during Subprocess Cleanup**:
   - Asynchronous test subprocesses in Windows proactor event loop occasionally emit `PytestUnraisableExceptionWarning: Exception ignored in: BaseSubprocessTransport.__del__` due to asynchronous pipe closing after loop teardown.
2. **Default Memory Database Concurrency in Tests**:
   - Orchestrator defaults to `data/memory.db`. Tests creating an Orchestrator without passing `memory_manager=MemoryManager(db_path=":memory:")` could leave persistent artifacts in `data/memory.db`.
3. **Hard-Coded Working Directory Dependencies**:
   - File explorer and project finders rely on `c:\Users\Project\Jarvis`. In production distribution, paths must resolve dynamically relative to `%APPDATA%\Shivani` and user profiles.

---

## 5. Security Risks

1. **External Content Ingestion (High Risk)**:
   - Malicious websites or poisoned GitHub repositories could embed adversarial instructions designed to hijack the planner (Indirect Prompt Injection).
2. **Path Traversal & Symlink Attacks (Medium Risk)**:
   - File manipulation tools must validate that targets do not escape authorized workspaces via `..` or junction links.
3. **Unsanitized Shell Execution (High Risk)**:
   - Shell command execution must undergo strict tokenization, argument checking, and privilege verification before dispatch.
4. **Credential Exposure (Critical Risk)**:
   - Real credentials (API keys, GitHub tokens, passwords) must be stored exclusively via Windows DPAPI / Credential Manager, never in plaintext configs or memory tables.

---

## 6. Dependency & Supply-Chain Risks

- `playwright`: High-performance browser engine, requires browser binary installations.
- `psutil`: Native C-extension on Windows, must be securely packaged.
- `faster-whisper`: Relies on ctranslate2 / local PyTorch runtime; needs clean local fallback if models are not pre-downloaded.
- `cryptography`: Essential for HMAC and DPAPI encryption; versions must be pinned.

---

## 7. Performance & Latency Risks

- Browser DOM extraction can introduce 500ms-1500ms latency on script-heavy pages.
- Whisper STT on CPU can introduce 1-3s latency for multi-sentence audio; needs quantization (int8).
- SQLite memory queries under 10,000 records are sub-millisecond, but require periodic TTL expiration purges.

---

## 8. Testing Gaps

- Missing dedicated prompt injection test suite (simulated malicious web pages, malicious emails, poisoned READMEs).
- Missing path traversal and command injection test suite.
- Missing crash-recovery & offline fallback test suite.
- Missing end-to-end user journeys (Tests 1–10 from master specification).

---

## 9. Packaging Gaps

- No PyInstaller / InnoSetup build specification to compile SHIVANI into a standalone `.exe`.
- No standard `%APPDATA%\Shivani` layout manager for clean configuration, logging, memory, and cache isolation.
- No uninstall script to clean user state safely upon request.

---

## 10. Recommended Changes for Phase 9

1. **Implement Dedicated Security Subsystem (`security/`)**:
   - 5-tier Risk Classifier (`SAFE`, `LOW_RISK`, `SENSITIVE`, `HIGH_RISK`, `CRITICAL`).
   - `SecretManager` with Windows DPAPI / keyring support.
   - `PromptInjectionClassifier` with untrusted data isolation.
   - `FilesystemPolicy` & `PathValidator` preventing traversal.
   - `CommandValidator` and `CommandSandbox`.
2. **Implement Backup & Recovery Subsystem (`recovery/`)**:
   - `BackupManager`, `RollbackManager`, `TransactionManager`, and `CheckpointManager`.
   - Automatic pre-action file snapshots with 1-click rollback.
3. **Implement Observability & Diagnostics (`observability/`)**:
   - Metrics, tracing, performance profiling, and `shivani doctor --full`.
4. **Implement Local & Offline Model Abstraction**:
   - `OllamaProvider`, `OpenAICompatibleProvider`, and offline-first core fallback.
5. **Implement Production CLI (`core/cli/main.py`)**:
   - Expose `shivani` command with full diagnostic, task, and lifecycle controls.
6. **Implement Windows Packaging & Installer Scripts (`packaging/`)**:
   - PyInstaller spec, portable zip generator, and InnoSetup/NSIS installer script.
7. **Expand Automated Test Suite**:
   - Security tests, prompt injection tests, crash recovery tests, and end-to-end verification.
