# SHIVANI 1.0 — 13-Step Real-World Demonstration Script

This script walks through an end-to-end, reproducible live demonstration of **SHIVANI 1.0** on Windows 11.

---

### Step 1: Health Diagnostic & Diagnostics
**Objective**: Demonstrate environment validation and hardware readiness.
```powershell
shivani doctor
```
- **Expected Output**:
  - `[OK] Python 3.12.x Environment`
  - `[OK] SQLite Storage & Migrations`
  - `[OK] Security Policy Engine`
  - `[OK] 190 Tools Registered`
  - `[OK] ALL SYSTEMS GO`

---

### Step 2: System Status & Topology
**Objective**: Verify system services, tool registry, and permissions.
```powershell
shivani status
```
- **Expected Output**: Status: `ONLINE`, Memory Engine: `READY`, Permission Policy: `STRICT_ENFORCE`.

---

### Step 3: Desktop UI & Server Launch
**Objective**: Start the local FastAPI server and UI dashboard.
```powershell
shivani start --host 127.0.0.1 --port 8000
```
- **Verification**: Open browser at `http://localhost:8000` to inspect:
  - Real-time task view
  - Active permissions monitor
  - Security audit log
  - Artifact gallery

---

### Step 4: Voice & Hindi/Hinglish Wake Command
**Objective**: Voice activation and natural Hinglish intent understanding.
- **Voice Trigger**: "Suno Shivani, mera current workspace status check karo."
- **Expected Output**:
  - Wake word recognized (`Suno Shivani`).
  - Hinglish translated to intent `system.status`.
  - Audio TTS response: "All systems are operating normally. 190 tools registered."

---

### Step 5: Autonomous File & Workspace Management
**Objective**: Safe file creation and directory boundary enforcement.
- **Command**: "Shivani, create a new notes file in workspace called release_notes.txt with today's date."
- **Verification**:
  - `release_notes.txt` created inside `workspace/`.
  - Attempting to write outside `workspace/` (e.g. `C:\Windows`) is intercepted and rejected with a `PermissionDenied` alert.

---

### Step 6: Safe Terminal Execution
**Objective**: Sandboxed command execution with risk-tier classification.
- **Command**: "Run `git status` and show recent commit hashes."
- **Verification**:
  - Risk Level assessed as `SAFE`.
  - Output captured and displayed cleanly.
  - Commands containing destructive tokens (`rmdir /s`, `format`) prompt for interactive approval or are blocked.

---

### Step 7: Computer Vision & Screen Inspection
**Objective**: Real display capture and active window introspection.
- **Command**: "Shivani, take a screenshot and inspect which application currently has focus."
- **Verification**:
  - Real PNG screenshot generated and saved to `workspace/shivani-artifacts/logs/`.
  - Foreground window title, geometry, and process ID returned.

---

### Step 8: Autonomous Browser Control
**Objective**: Headless or headed Chromium web navigation and structured extraction.
- **Command**: "Shivani, open the documentation page and verify the header title."
- **Verification**:
  - Playwright Chromium launches.
  - Page is loaded and DOM accessibility tree inspected.
  - Title and content extracted; malicious prompt injection payloads in web text isolated safely.

---

### Step 9: Long-Term Memory & Credential Redaction
**Objective**: Cross-session user preferences and automated secret scrubbing.
- **Command**: "Remember that my staging API token is sk-ant-api03-abcdef1234567890abcdef and my deployment region is ap-south-1."
- **Verification**:
  - Preference saved to SQLite memory.
  - Raw secret scrubbed: `sk-ant-***[REDACTED]***`.
  - Subsequent recall returns region `ap-south-1` without leaking unmasked secret keys.

---

### Step 10: Autonomous Coding Agent (TDD Bug Fix)
**Objective**: Automatic code diagnosis, patching, and git safety.
- **Command**: "Shivani, run the test suite for module math_lib, find the failing test, and patch it."
- **Verification**:
  - Pytest detects failing assertion.
  - Coding agent isolates diff and applies minimal surgery.
  - Re-runs tests to verify pass (`1 passed in 0.05s`).
  - Leaves git repo clean with no unauthorized commits or pushes.

---

### Step 11: Production Presentation (.pptx) Deck Builder
**Objective**: Autonomous deck generation with slides, pitch scripts, and judge Q&A.
- **Command**: "Shivani, generate a hackathon presentation deck for our project."
- **Verification**:
  - PowerPoint file `shivani_1.0_pitch_deck.pptx` generated.
  - 6 styled slides with speaker notes.
  - Multi-duration pitch scripts (30s, 1m, 3m, 5m) generated.
  - 8-category anticipated judge Q&A synthesized.

---

### Step 12: Scheduled Automation Workflow
**Objective**: Natural language routine creation and preview.
- **Command**: "Every weekday at 8 AM summarize my unread emails."
- **Verification**:
  - DSL generates recurring cron trigger (`MON, TUE, WED, THU, FRI at 08:00`).
  - Human-readable preview displayed.
  - Automation registered in SQLite store; can be paused or disabled with one click.

---

### Step 13: Emergency Kill-Switch & Clean Resumption
**Objective**: Instant abort of running autonomous actions.
- **Action**: Press Emergency Stop shortcut (`Ctrl+Alt+Shift+K`) or call `/api/emergency/stop`.
- **Verification**:
  - Active autonomous task halts immediately.
  - Task state marked `CANCELLED`.
  - Subsequent tool executions blocked until explicit operator resumption (`shivani resume`).
