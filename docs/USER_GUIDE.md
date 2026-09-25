# SHIVANI 1.0 — User Guide & Operations Manual

Welcome to **SHIVANI 1.0**, your voice-first, multimodal, secure personal AI operating layer for Windows.

---

## 1. Overview & System Capabilities
Shivani connects directly to your desktop environment to assist with complex, multi-step workflows while enforcing strict privacy and security boundaries:
- **Voice-First Interaction**: Hands-free operation with natural English and Hindi/Hinglish speech understanding.
- **Computer Autonomy**: Operating Windows applications, typing, clicking, capturing screenshots, and managing files safely.
- **Browser Automation**: Playwright-powered autonomous navigation, search, data extraction, and form filling with prompt-injection defense.
- **Autonomous Coding & Git Agent**: Diagnosing failing tests, writing surgical code fixes, running linters, and managing git branches safely.
- **Presentation Deck Builder**: Creating production-ready PowerPoint (`.pptx`) decks with multi-duration pitches and judge Q&A bundles.
- **Knowledge OS & Semantic Memory**: Indexing local repositories, notes, and documents with automatic secret scrubbing.
- **Proactive Automations**: Scheduling recurring tasks using plain English.
- **Air-Gapped & Offline Honesty**: Automatic fallback to local tools and deterministic routines when offline.
- **Emergency Kill Switch**: Instant stop mechanism (`Ctrl+Alt+Shift+K`) that cancels all active agent actions immediately.

---

## 2. Installation & Quickstart

### Prerequisites
- Windows 11 (or Windows 10 Build 19041+)
- Python 3.10+ (Recommended: Python 3.12 via `uv`)
- Microsoft Visual C++ 2015–2022 Redistributable
- Active Audio Microphone and Speakers (for voice features)

### Step 1: Install Dependencies
```powershell
# Using uv (recommended)
uv venv .venv --python 3.12
.venv\Scripts\activate
uv pip install -e .
```

### Step 2: System Health Check
Run the built-in diagnostic tool to verify all system components:
```powershell
shivani doctor
```

### Step 3: Launch Shivani
Start the Shivani daemon and desktop interface:
```powershell
shivani start
```
By default, the web control interface is available at `http://localhost:8000`.

---

## 3. Voice Control & Hinglish Commands

### Wake Words
Shivani listens continuously for:
- `"Shivani"`
- `"Hey Shivani"`
- `"Suno Shivani"`

### Multilingual & Hinglish Support
Shivani understands English, Hindi, and mixed Hinglish commands naturally:
- *"Shivani, open VS Code and run the unit tests."*
- *"Suno Shivani, mera current workspace check karo."*
- *"Shivani, ye test file fix kar do."*
- *"Shivani, summarize my unread notifications."*

---

## 4. Computer & Browser Autonomy

### Operating Applications
You can ask Shivani to interact with any desktop window:
- *"Open Notepad and write a summary of the meeting."*
- *"Switch to Chrome and refresh the tab."*
- *"Take a screenshot of the main monitor."*

### Browser Workflows
Shivani uses Playwright for web tasks:
- *"Research latest Python 3.12 features and save findings to research.md."*
- *"Open GitHub and check the open issues on our repository."*

---

## 5. Coding Agent & Safe Git Operations
Shivani acts as an autonomous pair-programmer:
- **Test-Driven Fixes**: Automatically runs `pytest`, locates failing assertions, patches source code, and verifies that tests pass.
- **Git Safety Guarantees**:
  - Never executes `git push` without interactive human approval.
  - Never creates unapproved commits on `main`/`master` branches.
  - Generates clear diffs for your review.

---

## 6. Presentations & Pitch Deck Generator
Generate complete PowerPoint decks in seconds:
```powershell
shivani presentation --title "My Next Startup" --duration 5 --mode hackathon
```
The output includes:
- Styled `.pptx` presentation deck.
- Pitch scripts tailored for 30s, 1m, 3m, and 5m presentations.
- Anticipated judge Q&A across 8 critical dimensions.

---

## 7. Knowledge OS & Memory Management
Shivani keeps your files and preferences organized:
- **Local Indexing**: Automatically parses `.py`, `.md`, `.txt`, `.pdf`, and `.docx` files.
- **Isolated Projects**: Project memory is isolated so context from one workspace does not bleed into another.
- **Automatic Secret Redaction**: Detects and redacts API keys, credentials, and passwords from logs and memory entries automatically.

---

## 8. Automations & Scheduling
Set up routines using natural language:
- *"Every weekday at 8 AM summarize my unread emails."*
- *"Check for git repository changes every 30 minutes."*

Manage registered routines via CLI:
```powershell
shivani automation list
shivani automation disable <id>
shivani automation enable <id>
```

---

## 9. Security, Permissions & Emergency Stop

### Risk Tiers
Every action is classified before execution:
1. `SAFE`: Read-only actions (inspecting windows, reading local project files). Executed automatically.
2. `LOW_RISK`: Reversible file edits inside designated `workspace/`.
3. `HIGH_RISK`: External API modifications, dependency installations. Requires explicit operator confirmation.
4. `CRITICAL`: Destructive actions (`format`, `rmdir /s /q`, modifying Windows system folders). Blocked by default.

### Emergency Kill Switch
If Shivani is performing an unwanted action:
- **Keyboard Shortcut**: Press `Ctrl+Alt+Shift+K`.
- **CLI**: Run `shivani stop --emergency`.
- **API**: Send a `POST` request to `http://localhost:8000/api/emergency/stop`.

To resume normal operations after verifying system state:
```powershell
shivani resume
```

---

## 10. Troubleshooting & Support

| Symptom | Common Cause | Resolution |
|:---|:---|:---|
| `ImportError: DLL load failed` | Virtualenv missing Windows system32 paths | Run via `uv run shivani` or run `shivani doctor` |
| Wake word not recognized | Microphone muted or low input gain | Check Windows Sound settings; verify Intel SST / Realtek mic |
| Web search reports offline | Network disconnected or offline mode enabled | Run `shivani doctor` to check internet status |
| `PermissionDenied` error | Action attempted outside sandbox boundary | Check configured workspace paths in `config.yaml` |

For diagnostics and detailed logs, consult:
`~/.shivani/logs/shivani.log`
