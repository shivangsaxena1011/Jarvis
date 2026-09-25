# SHIVANI 1.0 — Phase 20.5 Real-World Acceptance & Release Certification Plan

## 1. Objective
Validate the real-world operational readiness of **SHIVANI 1.0** on the actual physical host machine, verifying that the 20 completed engineering phases function in reality, not merely in automated unit test assertions.

---

## 2. Real Host Environment
- **Operating System**: Windows 11 Home/Pro Build 10.0.26200 (x86_64)
- **Python**: CPython 3.12.13 (uv-managed runtime)
- **CPU**: Intel Core Processor (12 cores, 14 logical threads)
- **RAM**: 16.59 GB Total (~5.9 GB Available)
- **Disk**: 402.82 GB Total (~153.6 GB Available)
- **GPU**: Intel(R) Graphics (2 GB shared VRAM)
- **Audio Devices**: Realtek High Definition Audio, Intel Smart Sound Technology Digital Microphones
- **Installed Browsers**: Google Chrome (`C:\Program Files\Google\Chrome\Application\chrome.exe`), Microsoft Edge (`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`)
- **Internet Status**: AVAILABLE (HTTP/HTTPS to Google/Cloud endpoints active)
- **Local AI Runtimes (Ollama)**: NOT FOUND on system PATH (must be reported as `NOT AVAILABLE` / Local Rule Fallback)
- **Android ADB**: NOT FOUND on system PATH (must be reported as `NOT AVAILABLE` / Mock or Emulated Mesh Test)

---

## 3. Real-World Execution Categories & Distinction Rules
Every test in this phase is categorized as one of:
- `REAL MACHINE TEST`: Executed against physical host OS, actual filesystem, real GUI, network, or actual hardware device.
- `AUTOMATED TEST`: Ran as a pytest assertion against internal code paths.
- `MOCK TEST`: Safely simulated dependency when real external device/service is genuinely absent.
- `MANUAL TEST`: Operator-driven verification of human interface elements.
- `NOT TESTED`: Capability deliberately skipped due to safety/operator instructions.
- `NOT AVAILABLE`: Hardware/tool dependency not present on this machine (e.g. Ollama, physical phone over ADB).

---

## 4. Test Matrix & Scope
1. **Application Lifecycle**: Startup, status, health endpoints, doctor check, shutdown, restart.
2. **First-Run Experience**: Clean isolated profile configuration initialization.
3. **Desktop Server & Interface**: Real REST and SSE endpoints (`/health/live`, `/health/ready`, `/status`, `/metrics`).
4. **Voice & Wake Word Pipeline**: Audio device enumeration, STT transcription, TTS synthesis, Hindi/Hinglish tokenization.
5. **Emergency Kill-Switch**: `EmergencyController` halting real tasks and blocking new action execution.
6. **Computer Control & Autonomy**: Launching Notepad, typing text, saving to a temporary directory, verifying filesystem artifact, taking screenshot.
7. **Filesystem Safety & Boundary Protection**: Workspace boundary enforcement, path traversal rejection.
8. **Terminal Sandboxing**: Harmless command execution (`python --version`, `git --version`, `echo Shivani`), risk classification.
9. **Browser Automation**: Playwright headless/headed browser navigation, DOM inspection, element click, prompt-injection isolation on local HTML.
10. **Memory & Knowledge**: Remembering user facts, recalling by key, secret redaction, SQLite persistence.
11. **Coding Agent**: Harmless bug injection in a temporary git repository, automated inspection, diff, test, fix.
12. **Presentation Agent**: PowerPoint generation, slide rendering, inspection of slide count and text contents.
13. **Model Routing & Offline Mode**: Evaluation of hybrid router, forced offline mode, honest refusal of live web data while offline.
14. **Data Governance & Portability**: Backup creation, SHA-256 manifest verification, user data JSON export, confirmed zero-trace wipe.
15. **Full Regression Verification**: Complete automated test suite re-execution (all 496 tests).

---

## 5. Safety Invariants
- Never delete or overwrite personal user files outside designated temporary test sandboxes (`tempfile.TemporaryDirectory()`).
- Never send real emails or trigger real social media posts.
- Never push to external GitHub remotes during acceptance testing.
- Never fake test results: missing hardware must be honestly reported as `NOT AVAILABLE`.
