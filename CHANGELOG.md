# Changelog

All notable changes to the **SHIVANI Personal AI Operating Layer** are documented in this file.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-25

### Phase 20: Final Integration, Hardening, Red-Team Matrix & Production Release (Shivani 1.0)
- **Master Architecture & System Map**: Formally unified all 20 subsystems into the authoritative `SHIVANI_MASTER_ARCHITECTURE.md`.
- **Extended Task Lifecycle**: Integrated `PAUSED` and `BLOCKED` states across the core orchestrator state machine and task manager.
- **Stuck Task Detection**: Implemented `TaskWatchdog` proactively detecting runaway loops, repeated consecutive action errors, timeout stalls, and step limit violations.
- **Authoritative Kill-Switch**: Implemented `EmergencyController` supporting instant global action suspension, task cancellation, and safe recovery.
- **Scoped Approvals**: Introduced `ApprovalScope` (`ONE_ACTION`, `TASK_SCOPE`, `WORKFLOW_SCOPE`, `TIME_LIMITED`) in `PermissionEngine` and `PolicyEngine` with automated expiration and single-use consumption.
- **Data Governance & Portability**: Built `BackupManager` (with SHA-256 integrity verification and zip-slip prevention) and `DataManager` (portable JSON/ZIP export and GDPR-compliant zero-trace data deletion).
- **CLI Extensions**: Added `shivani data export`, `shivani data delete`, `shivani data backup`, `shivani data verify`, `shivani data restore`, and `shivani data list`.
- **Production Observability**: Added `/health/live`, `/health/ready`, and `/metrics` endpoints to the desktop REST server.
- **Adversarial Red-Team Matrix**: Established a 17-test suite covering prompt injection, tool injection, DPAPI secret security, memory poisoning, and kill-switch verification.
- **Deployment Scripts**: Added PowerShell installation and uninstallation automation (`scripts/install.ps1`, `scripts/uninstall.ps1`).

---

### [0.19.0] - Phase 19: Local AI, Model Routing, Performance Engineering & Offline Autonomy
- Dynamic hybrid model routing (`local_first`, `cloud_first`, `privacy_first`, `speed_first`, `cost_aware`).
- Ollama local inference adapter with hardware profiling (VRAM, CPU, memory).
- Automated fallback cascade from local to cloud to deterministic rule-based engines.
- Offline Mode guaranteeing zero cloud leakage for private and sensitive tasks.
- Benchmarking suite measuring TTFT (time-to-first-token), tokens/sec, and routing latency.

### [0.18.0] - Phase 18: Cross-Device Continuity, Device Orchestration & Ambient Intelligence
- Device Mesh Protocol with HMAC-SHA256 authenticated peer-to-peer transport.
- Cryptographic 6-digit numeric pairing exchange with replay attack prevention.
- Seamless task handoff preserving execution checkpoints and context between PC and phone.
- Secure chunked file and clipboard synchronization across trusted mesh devices.
- Mesh-wide emergency kill-switch broadcasting halts across all paired nodes.

### [0.17.0] - Phase 17: Advanced Computer Autonomy, GUI Reasoning & Long-Horizon Control
- Closed-loop observe-act-verify desktop automation cycle.
- Unified desktop state representation combining window hierarchy, coordinate maps, and OCR.
- Self-correcting GUI recovery engine for dialog dismissals and missed clicks.
- Deterministic synthetic desktop mock for CI testing without physical display dependencies.

### [0.16.0] - Phase 16: Personal Agent, Goals, Projects, Task Intelligence & Productivity OS
- Hierarchical productivity data model (`Goal`, `Project`, `Task`, `Review`).
- Morning briefing, daily time blocking, and weekly retrospective engines.
- Proactive deadline tracking, priority scoring, and task deferral recommendations.
- Interactive productivity CLI commands (`shivani goal`, `shivani project`, `shivani plan`).

### [0.15.0] - Phase 15: Proactive Intelligence, Background Sensing & Autonomous Scheduling
- Event-driven background triggers monitoring file changes, idle time, and calendar events.
- Cron and recurring task scheduling engine with persistent state tracking.
- Proactive suggestion generation with cooldown and user frequency throttling.

### [0.14.0] - Phase 14: Desktop Human Interface & HUD
- FastAPI desktop web server with Server-Sent Events (SSE) and WebSocket broadcasts.
- Reactive HUD widget displaying assistant thinking state, active agent, and step progress.
- Notification center with multi-category filtering, prioritization, and dismissal.

### [0.13.0] - Phase 13: Universal Skills & Dynamic Plugin System
- Dynamic skill discovery from `%APPDATA%\Shivani\skills` and workspace directories.
- Sandboxed skill manifest validation and capability permission declarations.
- Live reload of user-defined skill routines without restarting the runtime.

### [0.12.0] - Phase 12: Personal Knowledge OS
- Dual-layer knowledge engine combining relational SQLite metadata with vector embeddings.
- Entity extraction and semantic relationship graph connecting people, projects, and topics.
- Hybrid search merging lexical BM25 matching and dense vector similarity.

### [0.11.0] - Phase 11: Advanced Planning, Hierarchical Decomposition & Checkpoints
- Hierarchical task planner decomposing natural language queries into directed acyclic graphs (DAGs).
- Pre-execution validation, contingency planning, and failure recovery branches.
- State checkpointing enabling rollback and resumption of interrupted plans.

### [0.10.0] - Phase 10: Multimodal Vision, Screen OCR & Grounding
- High-resolution screen capture pipeline with multi-monitor geometry support.
- Local OCR engine utilizing Tesseract and Windows Media OCR for text extraction.
- Visual element grounding mapping text queries to exact click coordinates.

### [0.9.0] - Phase 9: Security Sandbox, DPAPI Secret Storage & Policy Enforcement
- Windows DPAPI credential encryption storing API keys with zero plaintext exposure.
- Strict filesystem safety enforcing boundary validation against path traversal attacks.
- Three-tier permission engine (SAFE, SENSITIVE, CRITICAL) requiring explicit user confirmation.

### [0.8.0] - Phase 8: Multi-Agent Orchestration & Subagent Delegation
- Specialized autonomous subagents (Research, Coding, Desktop, Document).
- Inter-agent message bus enabling collaborative problem solving.
- Isolated workspace branching preventing concurrent subagent modifications.

### [0.7.0] - Phase 7: Hierarchical Long-Term Memory
- Multi-tier memory architecture (Short-Term, Working Context, Episodic, Semantic).
- Automatic secret redactor scrubbing credentials before persistent storage.
- User preference resolution with explicit user overrides and confidence decay.

### [0.6.0] - Phase 6: Android Companion App Integration
- Secure local WebSocket bridge between desktop runtime and Android companion.
- Remote device status inspection, notification mirroring, and quick command dispatch.

### [0.5.0] - Phase 5: Coding & Research Autonomous Agents
- Codebase exploration, file editing, syntax verification, and automated test execution.
- Web search synthesis and multi-source document summarizing capabilities.

### [0.4.0] - Phase 4: Productivity Integrations & Presentation Generation
- Calendar, email, and task management integration adapters.
- Automated PowerPoint presentation generator (`python-pptx`) from outline data.

### [0.3.0] - Phase 3: Browser Automation Subsystem
- Playwright-powered headless and headed browser control.
- DOM extraction, form filling, screenshot verification, and session persistence.

### [0.2.0] - Phase 2: Windows Computer Control
- Native keyboard and mouse automation via PyAutoGUI and pywinauto.
- Foreground window management, process inspection, and display monitor detection.

### [0.1.0] - Phase 1: Core Runtime, LLM Abstraction & Voice Subsystem
- Asynchronous task orchestrator and event bus foundation.
- Multi-provider LLM abstraction layer supporting Anthropic, OpenAI, Gemini, and Ollama.
- Voice pipeline with streaming wake word detection and speech-to-text transcription.
