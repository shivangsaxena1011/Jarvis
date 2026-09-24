# SHIVANI AI — Phase 17 Computer Autonomy & GUI Reasoning Audit

## 1. Executive Summary

This audit assesses the state of computer-use capabilities across Phases 1–16 of **SHIVANI**, inventories existing OS, desktop, vision, and planning modules, identifies gaps between rudimentary coordinate-clicking and genuine **closed-loop computer autonomy**, and defines the architectural blueprint for **Phase 17: Advanced Computer Autonomy, GUI Reasoning & Long-Horizon Desktop Control**.

---

## 2. Inventory of Existing Subsystems & Reusability Assessment

| Subsystem | Existing Implementation | Reusability in Phase 17 | Phase 17 Extension Required |
|---|---|---|---|
| **OS Abstraction** | `tools/desktop/os/` (`windows.py`, `mock.py`, `base.py`) | **High**: Win32 window management, mouse/keyboard input synthesis, process lifecycle. | Add Windows UI Automation (UIA) tree inspection, control patterns, and DPI scaling normalization. |
| **Window & App Managers** | `tools/desktop/window.py`, `application.py` | **High**: Resolving executable paths, launching apps, focusing/maximizing/minimizing windows. | Add application recognition (`ApplicationContext`), application state machines, and multi-monitor layout geometry. |
| **Input Controller** | `tools/desktop/input.py` (`InputController`) | **High**: Mouse clicks, drag, text typing, hotkeys with focus-check safeguards. | Add confidence-aware action execution, expectation engine verification, and drag-and-drop state verification. |
| **Screen Capture** | `tools/desktop/screen.py`, `vision/capture/` | **High**: Multi-monitor screenshots, active window capture, coordinate transformers. | Add real-time visual delta calculation, ROI (Region of Interest) visual cropping, and privacy redaction. |
| **Vision & Grounding** | `vision/grounding/`, `vision/ui/`, `vision/ocr/` | **High**: Optical character recognition (Tesseract/Mock), visual element detector, bounding boxes. | Add multi-source UI fusion (UIA + DOM + OCR + Vision + Spatial), UI semantic graph, and spatial reasoning predicates. |
| **Terminal System** | `tools/terminal/shell_tools.py` | **Moderate**: Basic command execution via shell. | Add full terminal autonomy, command safety classifier (safe vs. dangerous), streaming output capture, and error diagnostic parser. |
| **Clipboard Control** | `tools/desktop/clipboard.py` | **High**: Reading and setting system clipboard via `pyperclip` or Win32. | Add clipboard safety filter (redaction of tokens, API keys, passwords) and transactional restore. |
| **Browser Automation** | `tools/browser/` (Playwright-based) | **High**: DOM inspection, element clicks, page navigation. | Add dynamic Browser <-> Computer handoff (DOM interaction preferred, GUI/vision fallback). |
| **Planner & Tasks** | `core/planner/`, `core/productivity/` | **High**: Task DAGs, dependency evaluation, multi-agent handoffs. | Add long-horizon computer task DAGs, dynamic replanning on external state changes, and progress loop detection. |
| **Recovery & Checkpoints** | `recovery/checkpoint_manager.py` | **High**: State snapshotting and rollback primitives. | Add computer task checkpoints (app state, UI tree, completed actions, file diffs) and safe resume logic. |
| **Security & Permissions** | `security/permissions/engine.py` | **High**: Risk-tiered permission checks and confirmation gates. | Integrate computer action priority (Emergency Stop > Direct Command > Background Automation) and modal dialog protection. |

---

## 3. Key Deficiencies in Current Implementations & Phase 17 Solutions

1. **Open-Loop Execution vs. Closed-Loop Autonomy**:
   - *Previous*: Scripts issue clicks or key presses with static sleeps and assume success.
   - *Phase 17*: True closed loop: `Observe -> Understand -> Plan -> Act -> Observe -> Verify -> Recover/Replan -> Continue`. Every action verifies its expected post-condition before proceeding.
2. **Coordinate Dependency vs. Semantic Grounding**:
   - *Previous*: Prone to clicking coordinates that drift across screen resolutions, themes, or window movements.
   - *Phase 17*: Multi-source fusion (UIA control pattern -> DOM -> OCR -> Vision -> Spatial relation -> Coordinate fallback). Reasoning operates on semantic targets (e.g. *"Click Save in the toolbar"*).
3. **Blind Retries vs. Adaptive Recovery**:
   - *Previous*: Repeatedly re-trying the exact same action when an element is missing.
   - *Phase 17*: Error classification (`UI_CHANGED`, `ELEMENT_NOT_FOUND`, `APPLICATION_ERROR`, `AUTH_REQUIRED`) mapped to adaptive strategies (re-observe, fallback to keyboard shortcuts, semantic search, or human takeover).
4. **Lack of Application-Specific Semantics**:
   - *Previous*: Every application is treated as an undifferentiated canvas of pixels.
   - *Phase 17*: `ApplicationAdapter` architecture providing specialized semantic hooks for VS Code, Windows Explorer, Terminal, Excel, Word, PowerPoint, Chrome/Edge, and Notepad, while maintaining a robust generic fallback.
5. **Safety & External State Disruption**:
   - *Previous*: If a user moves a window or types into an editor while an agent is running, the agent can cause severe confusion or data destruction.
   - *Phase 17*: External state difference detection, resource locking (`Desktop`, `Terminal`, `VSCode`), emergency pause (`"Shivani stop"`), and safe manual takeover.

---

## 4. Phase 17 Architectural Blueprint

```text
                               ┌────────────────────────────────────────────────────────┐
                               │                 MASTER ORCHESTRATOR                    │
                               └───────────────────────┬────────────────────────────────┘
                                                       │
                                                       ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       COMPUTER AUTONOMY AGENT                                         │
│                                  (core/computer/agent.py)                                             │
├───────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────────┤
│ Observation Engine│ Semantic Graph    │ Visual Grounding  │ Expectation Engine│ Execution Engine      │
│ (UIA + OCR +      │ (Hierarchical UI  │ (Multi-source     │ (Pre/Post diff,   │ (Closed-loop observe/ │
│  Vision + Window) │  Spatial Engine)  │  Confidence Gate) │  Expected states) │  act/verify cycle)    │
├───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────────┤
│ Recovery Engine   │ Checkpoint Engine │ Resource Lock     │ Terminal Engine   │ App Adapter Registry  │
│ (Loop detect,     │ (Safe resume,     │ (Priority &       │ (Safety filter,   │ (VS Code, Explorer,   │
│  Dynamic replan)  │  Rollback state)  │  Takeover)        │  Output parser)   │  Office, Browsers)    │
└───────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────────┘
                                                       │
                           ┌───────────────────────────┴───────────────────────────┐
                           ▼                                                       ▼
              ┌──────────────────────────┐                           ┌──────────────────────────┐
              │    SYNTHETIC GUI TEST    │                           │    WINDOWS 11 DESKTOP    │
              │       ENVIRONMENT        │                           │  UIA, Win32, Input, Screen│
              └──────────────────────────┘                           └──────────────────────────┘
```

---

## 5. Security & Boundary Guardrails

1. **No Autonomy Bypasses**: Autonomy will never bypass authentication, CAPTCHAs, MFA, or security permissions. When authentication or human verification appears, the agent enters a clean `AUTH_PAUSED` state.
2. **Terminal Command Safety**: Dangerous commands (`rm -rf`, `format`, `del /f /q`, registry edits, credential harvesting) require explicit interactive user approval.
3. **Clipboard Privacy**: Passwords, OTPs, private keys, and tokens detected in clipboard contents are automatically masked and excluded from persistent logging.
4. **Action Budgeting**: Every computer task operates within a strict resource budget (`max_actions`, `max_runtime_seconds`, `max_retries`) to prevent runaways.
