# Agent Specifications — SHIVANI

SHIVANI utilizes specialized agent domain controllers coordinated by the central Orchestrator.

---

## 1. Computer Agent
- **Domain**: Operating system interactions, window state management, and display observation.
- **Tools**:
  - `computer.screenshot`: High-resolution screen capture.
  - `computer.get_active_window`: Foreground window detection and PID inspection.
  - `computer.list_processes`: Operating system process enumeration and memory stats.
  - `computer.open_app`: Application process launcher with verification check.
- **Verification Strategy**: Reads process tables via `psutil` and window handles via OS APIs to confirm expected foreground presence.

---

## 2. Browser Agent (Phase 4 Roadmap)
- **Domain**: Web automation and content extraction.
- **Primary Engine**: Playwright (Chromium / Chrome / Brave profiles).
- **Selector Hierarchy**:
  1. Accessibility tree / ARIA roles
  2. Semantic text selectors
  3. Stable CSS / XPath selectors
  4. Computer vision & screen coordinate fallback
- **Safety**: Uses existing authorized browser profiles; never bypasses anti-bot, CAPTCHA, or DRM systems.

---

## 3. Filesystem Agent
- **Domain**: Workspace file organization, inspection, and creation.
- **Tools**:
  - `filesystem.list_dir`: Safe directory traversal.
  - `filesystem.read_file`: UTF-8 text reader with byte limits.
  - `filesystem.write_file`: Atomic file writer with directory auto-creation.
  - `filesystem.safe_delete`: Guarded deletion requiring `CRITICAL` confirmation.
- **Safety**: Sandboxed path traversal checks prevent escaping authorized root folders.

---

## 4. Coding Agent (Phase 6 Roadmap)
- **Domain**: Software engineering, test execution, and repository maintenance.
- **Workflow**: UNDERSTAND → PLAN → EDIT → TEST → VERIFY → REPORT.
- **Safety**: Creates git checkpoints before broad edits; never touches `.env` secrets or exposed credentials.

---

## 5. Research Agent (Phase 7 Roadmap)
- **Domain**: Structured web inquiry, academic citation tracking, and fact synthesis.
- **Output**: Source-attributed research notes with Markdown citations.

---

## 6. Mobile Agent (Phase 8 Roadmap)
- **Domain**: Android device control via explicit pairing and ADB / UIAutomator bridge.
- **Companion**: *Shivani Mobile* Android application.
- **Safety**: Operates only over authenticated cryptographic session tokens.
