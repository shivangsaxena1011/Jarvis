# SHIVANI — Computer Use Agent & Windows Desktop Control

## Overview

The **Computer Use Agent** (`agents.computer.ComputerAgent`) provides autonomous, verified desktop operation for Windows 11. It allows SHIVANI to understand natural language instructions in both English and Hindi/Hinglish, plan multi-step execution graphs, operate applications, manipulate windows, control mouse and keyboard, search files, manage the clipboard, and capture screens with strict verification discipline.

---

## Core Principle: OBSERVE → PLAN → ACT → VERIFY

SHIVANI never assumes an action succeeded simply because a system call was dispatched. Every action undergoes rigorous environmental verification:

```
USER Instruction (Voice / Web / CLI)
  ↓
Orchestrator & Hinglish Normalizer
  ↓
Task Planner (Risk Assessment & Step Formulation)
  ↓
Computer Agent (Focus & Input Safety Validation)
  ↓
Operating System Adapter (Windows 11 Win32 / PyAutoGUI)
  ↓
Environmental Observation (Process Table, Win32 Window Rect, Visual Capture)
  ↓
Verification Check (Verified: True / False)
  ↓
User Response (Spoken Voice / Dashboard Timeline)
```

---

## Architecture & Component Breakdown

```
SHIVANI Desktop Control Architecture
├── agents/computer/
│   ├── agent.py               # ComputerAgent coordinator with retry & recovery
│   ├── observation.py         # DesktopObservation & DesktopElement models
│   ├── context.py             # CurrentUIContext tracking active window/target
│   ├── observer.py            # ScreenObserver producing structured observations
│   ├── vision.py              # VisionProvider interface & MockVisionProvider
│   └── browser_stub.py        # BrowserAgent stub detecting installed browsers
├── tools/desktop/
│   ├── os/                    # Isolated OS Abstraction Layer
│   │   ├── base.py            # OperatingSystemAdapter ABC
│   │   ├── windows.py         # Windows 11 native Win32/PyAutoGUI adapter
│   │   ├── mock.py            # Deterministic in-memory test adapter
│   │   └── factory.py         # Adapter factory & platform detection
│   ├── application.py         # ApplicationManager (discovery, launch, verify)
│   ├── window.py              # WindowManager (focus, minimize, maximize, close)
│   ├── input.py               # InputController with Focus Safety Checks
│   ├── screen.py              # ScreenCapture manager
│   ├── clipboard.py           # ClipboardManager with privacy protection
│   ├── app_tools.py           # computer.open_app, close_app, focus_app, list_apps, active_window
│   ├── window_tools.py        # window.list, focus, minimize, maximize, restore, close
│   ├── input_tools.py         # mouse_move, click, double_click, right_click, drag, scroll, type, press_key, hotkey
│   ├── clipboard_tools.py     # clipboard.read, write, clear
│   ├── screen_tools.py        # computer.screenshot
│   └── file_explorer_tools.py # computer.open_folder, computer.find_files
```

---

## Supported Commands

### 1. Application Control
- *"Shivani, open VS Code."* / *"VS Code kholo."* / *"VS Code pe jao."*
- *"Shivani, open Chrome."* / *"Chrome kholo."* / *"Chrome launch karo."*
- *"Shivani, open calculator."* / *"Calculator kholo."*
- *"Shivani, close Chrome."* / *"Chrome band karo."* / *"Isko close karo."*

### 2. Window Management
- *"Shivani, minimize Chrome."* / *"Chrome ko minimize karo."*
- *"Shivani, switch to VS Code."* / *"VS Code pe wapas jao."*
- *"Shivani, maximize VS Code."* / *"VS Code maximize karo."*
- *"Shivani, close this window."* / *"Current window band karo."*

### 3. File Explorer & Document Finding
- *"Shivani, open my Downloads folder."* / *"Downloads folder kholo."*
- *"Shivani, open Documents."* / *"Documents kholo."*
- *"Shivani, find my PDF files."* / *"PDF files dhundo."*

### 4. Input & Typing (with Target Window Focus Safety)
- *"Shivani, type hello world."* / *"Type karo hello."*
- *"Shivani, press Enter."*
- *"Shivani, press Ctrl+C."* / *"Hotkey send karo."*

### 5. Screen Capture & Observation
- *"Shivani, take a screenshot."* / *"Screenshot lo."* / *"Screenshot le lo."*

### 6. Emergency Stop
- *"Shivani stop."* / Clicking **STOP ALL** in the Dashboard: Immediately cancels active computer tasks, releases input hooks, and resets voice to `IDLE`.

---

## Input Safety Architecture

Before executing keyboard or mouse actions, `InputController` strictly validates the foreground target:
1. **Target Verification**: Checks whether the target window/application currently holds foreground focus.
2. **Automatic Refocus**: If another window has focus, it automatically refocuses the target window before typing or clicking.
3. **Safety Violation Shield**: If the target window does not exist on the system, it aborts execution and raises a descriptive `Input Safety Violation` error, preventing unintended input into wrong applications.

---

## Clipboard Privacy Protection

- `clipboard.read`, `clipboard.write`, and `clipboard.clear` tools allow safe interaction with the system clipboard.
- Clipboard contents are masked and never emitted into persistent audit files (`audit.jsonl`) or sent to remote LLM providers unless explicitly instructed.

---

## Multi-Tier Application Discovery

When locating applications on Windows 11, `ApplicationManager` does not rely solely on hardcoded paths:
1. **Known Aliases**: Fast paths for standard applications (Chrome, VS Code, Notepad, Calculator, Edge).
2. **Windows Registry App Paths**: Scans `HKLM` and `HKCU` `Software\Microsoft\Windows\CurrentVersion\App Paths`.
3. **Start Menu Shortcuts**: Walks `%APPDATA%\Microsoft\Windows\Start Menu\Programs` and `%ALLUSERSPROFILE%\Microsoft\Windows\Start Menu\Programs` for `.lnk` shortcuts.
4. **System PATH**: Resolves executables using `shutil.which`.

---

## Verification & Testing

Run all 60 automated unit and integration tests:
```powershell
.venv\Scripts\pytest.exe -v
```
All tests pass cleanly in ~24s with 100% test coverage for OS adapters, window managers, input safety, and computer agent tasks.
