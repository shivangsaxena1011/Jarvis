# SHIVANI — Personal Autonomous AI Computer Agent

> **Core Principle: OBSERVE → PLAN → ACT → VERIFY**

SHIVANI is a voice-first, autonomous personal AI operating layer designed to understand natural-language instructions (English and Hindi / Hinglish), formulate verified structured multi-step plans, operate the computer desktop, manipulate files safely, browse the web, interact with Android devices through a paired companion bridge, and assist with software development while enforcing strict three-tier permission sandboxing.

---

## Key Features

- **Autonomous Computer Operation**: Launch apps, inspect active windows, enumerate processes, capture desktop screenshots, and execute safe terminal commands.
- **Strict Verification Discipline**: Never assumes an action succeeded without verifying outcomes in the environment.
- **Three-Tier Permission Engine**:
  - `SAFE`: Non-destructive read and observation actions run automatically.
  - `SENSITIVE`: File modifications, git commits, and shell operations require policy approval.
  - `CRITICAL`: Destructive operations (file deletions, system process termination, irreversible disk changes) strictly require user confirmation.
- **Universal Autonomous Browser Agent (Phase 4)**:
  - Operates modern web applications via Playwright (`agents/browser/`, `tools/browser/`).
  - Implements the strict **OBSERVE ──▶ PLAN ──▶ ACT ──▶ VERIFY** paradigm.
  - Multi-browser channel management: Chrome, Microsoft Edge, Brave, and bundled Chromium with profile isolation.
  - 7-Tier natural-language element resolution (role/name, label, placeholder, test-id, visible text, semantic CSS, multimodal vision fallback).
  - YouTube search & playback workflow with title disambiguation via `SequenceMatcher` and verification of HTML5 `<video>` playback state.
  - Multi-engine search (Google, Bing, DuckDuckGo), noise-filtered webpage summarization, and structured data extraction.
  - Multi-tab lifecycle control (open, switch, close, list) and file upload/download verification.
  - Third-party integration foundations (`integrations/linkedin/`, `integrations/gmail/`) with mandatory human-in-the-loop confirmation.
- **Autonomous Computer Use Agent & Windows 11 Desktop Control**:
  - Operates Windows 11 applications (*"Shivani, open VS Code"*, *"Chrome kholo"*), multi-tier app discovery (Registry App Paths, Start Menu `.lnk`, PATH).
  - Window management: minimize (*"Chrome ko minimize karo"*), maximize, restore, focus/switch (*"VS Code pe wapas jao"*), and close.
  - Safe mouse movement, clicks, double/right-click, drag, scroll, and typing with **Input Safety Validation** (strictly verifies active target window focus before interacting).
  - File Explorer navigation (*"Downloads folder kholo"*) and direct pattern search (*"find my PDF files"*).
  - Screen capture (full desktop, active window, region) with `ScreenObserver` generating structured `DesktopObservation` models ready for vision.
  - Safe clipboard control (`clipboard.read`, `write`, `clear`) with zero secret leakage to audit logs.
- **Voice Pipeline & Wake Word ("Shivani")**:
  - Local wake word detection with RMS energy and phonetic matching.
  - Speech-to-Text via `faster-whisper` (CPU/int8 local inference) with automatic Hinglish/Hindi/English audio transcription.
  - Text-to-Speech via `edge-tts` with high-clarity feminine Indian voice (`hi-IN-SwaraNeural`) and local `pyttsx3` fallback.
  - Instant speech cutoff (<50ms) on `"Shivani stop"` voice interruption.
  - Multi-turn conversational context tracking previous subjects, applications, and clarification queries.
  - In-browser Push-to-Talk (PTT) with animated soundwave visualizer and live audio response playback.
- **Extensible LLM Provider Layer**: Pluggable drivers for Google Gemini (`gemini-2.5-flash`), OpenAI-compatible endpoints, and a deterministic offline Mock provider.
- **Redacting Audit Logger**: Logs every task, step, and verification in `audit.jsonl` with automatic masking of secrets, API keys, and passwords.
- **Emergency Stop System**: Immediate task abort via `"Shivani stop"` voice command, REST API, or the Desktop Dashboard **STOP ALL** button.
- **Futuristic Desktop Dashboard**: Dark-first, luminous interface with real-time WebSocket state streaming, timeline updates, and interactive approval cards.


---

## Repository Structure

```
shivanI/
├── agents/
│   └── computer/            # ComputerAgent, ScreenObserver, CurrentUIContext, BrowserStub
├── apps/
│   ├── desktop/             # FastAPI backend & futuristic Web Dashboard
│   └── mobile/              # Android companion specs & bridge
├── core/
│   ├── orchestrator/        # State machine, executor, emergency stop, planner
│   ├── context/             # Hinglish normalizer and session context
│   ├── llm/                 # Model provider abstractions (Gemini, OpenAI, Mock)
│   ├── config.py            # Settings loader & validation
│   └── memory/              # Context & memory structures
├── security/
│   ├── permissions/         # Risk classification & approval flow engine
│   ├── sandbox/             # Command risk classifier & path safety
│   └── audit/               # JSONL audit logger with secret redaction
├── tools/
│   ├── base.py              # BaseTool contract & ToolResult
│   ├── registry.py          # Central registry with timeout & verification
│   ├── desktop/             # OS abstraction (Windows 11), WindowManager, InputController
│   ├── computer/            # Foundation computer & process tools
│   ├── filesystem/          # List, read, write, safe delete
│   └── terminal/            # Sandboxed shell command execution
├── voice/                   # Wake word, faster-whisper STT, edge-tts TTS, pipeline
├── tests/                   # Full pytest automated test suite
├── docs/                    # Complete architecture, agents, tools & security docs
├── .env.example             # Configuration template
├── pyproject.toml           # Python dependencies & build config
└── main.py                  # Main CLI and server entrypoint
```

---

## Getting Started

### Prerequisites

- Python 3.12+ (CPython 3.12 recommended)
- `uv` package manager (or standard `pip`)

### 1. Clone & Setup Environment

```powershell
# Create virtual environment
uv venv --python 3.12 .venv

# Activate environment (Windows PowerShell)
.venv\Scripts\activate

# Install dependencies in editable mode
uv pip install -e ".[dev]"
```

### 2. Configure Environment

Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```

To enable Google Gemini, configure:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-flash
```

To configure Voice (Wake word, STT & TTS):
```env
VOICE_ENABLED=true
WAKE_WORD=Shivani
STT_PROVIDER=whisper         # faster-whisper on CPU/int8
STT_MODEL=tiny               # tiny, base, or small
TTS_PROVIDER=edge_tts        # edge_tts or pyttsx3
TTS_VOICE=hi-IN-SwaraNeural  # Clear feminine Indian voice
VOICE_CONFIDENCE_THRESHOLD=0.65
```

For offline testing without API keys or microphones, leave `LLM_PROVIDER=mock`, `STT_PROVIDER=mock`, and `TTS_PROVIDER=mock`.

---

## Running SHIVANI

### 1. Verification Dry-Run
```powershell
.venv\Scripts\python.exe main.py --dry-run
```

### 2. Single Task Execution (One-Shot CLI)
```powershell
.venv\Scripts\python.exe main.py --task "Shivani, list files"
```

### 3. Start Desktop Server & Futuristic Dashboard
```powershell
.venv\Scripts\python.exe main.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser to access the live dashboard.

### 4. Interactive Voice Control
- **Push-to-Talk (PTT)**: Click and hold the microphone icon in the web dashboard header to speak (e.g., *"Shivani, YouTube kholo"*). Release to process and hear SHIVANI's spoken reply.
- **Voice Interruption**: Click **STOP ALL** or say *"Shivani stop"* to immediately cut off speech and abort executing actions.
- **Voice Status**: Query `GET /api/voice/status` to view the real-time audio state (`IDLE`, `LISTENING`, `PROCESSING`, `SPEAKING`).

### 5. Windows Desktop Operation Examples
```powershell
# Open and verify applications
.venv\Scripts\python.exe main.py --task "Shivani, open VS Code"
.venv\Scripts\python.exe main.py --task "Shivani, open Chrome"

# Window management
.venv\Scripts\python.exe main.py --task "Shivani, minimize Chrome"
.venv\Scripts\python.exe main.py --task "Shivani, switch to VS Code"

# File Explorer & documents
.venv\Scripts\python.exe main.py --task "Shivani, open my Downloads folder"
.venv\Scripts\python.exe main.py --task "Shivani, find my PDF files"

# Screen observation
.venv\Scripts\python.exe main.py --task "Shivani, take a screenshot"
```

---

## Running Automated Tests

Run the complete test suite:
```powershell
.venv\Scripts\pytest.exe -v
```

---

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Computer Use Agent & Windows Control](docs/COMPUTER_AGENT.md)
- [Agent Specifications](docs/AGENTS.md)
- [Tool System & Contracts](docs/TOOLS.md)
- [Security & Sandbox Engine](docs/SECURITY.md)
- [Permissions & Approval Workflow](docs/PERMISSIONS.md)
- [Voice System](docs/VOICE.md)
- [Browser Agent Design](docs/BROWSER.md)
- [Android Companion Bridge](docs/ANDROID.md)
- [Memory Hierarchy](docs/MEMORY.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Testing & Quality Assurance](docs/TESTING.md)
- [Product Roadmap](docs/ROADMAP.md)

---

## License

MIT License. Designed and engineered for personal autonomous computer use.
