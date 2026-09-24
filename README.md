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
- **Productivity Integrations & Cross-Application Workflows (Phase 5)**:
  - **YouTube Integration** (`integrations/youtube`): Direct search, ranked candidates, playback controls (play, pause, resume, like, fullscreen) with verified HTML5 video state.
  - **Gmail Integration** (`integrations/gmail`): Categorized unread email triage (important, personal, work, promotional, spam), executive summaries, and two-stage safe cleanup proposal with approval gates.
  - **LinkedIn Integration** (`integrations/linkedin`): Local project showcase generation, DRAFT creation, user approval gate, and verified publication.
  - **GitHub Integration** (`integrations/github`): Local repo scanner, language/framework detection, runnable command analysis, file operations, and issue management.
  - **Autonomous Research Engine** (`integrations/research`): Multi-source querying, provenance tracking, structured citation extraction, and markdown/JSON report bundles (`report.md`, `sources.json`, `summary.json`).
  - **Content Synthesis Agent** (`agents/content`): High-impact social posts, email drafts, documentation, and README generation.
  - **Composable Workflow Engine** (`core/workflows`): Sequential execution, dynamic variable substitution (`{var}`), non-destructive pausing on approval (`WAITING_FOR_APPROVAL`), exact resumption, and environmental failure diagnostics.
- **Advanced Professional Agents & Checkpointed Long-Running Workflows (Phase 6)**:
  - **Coding Agent** (`agents/coding/`, `tools/coding/`): Follows strict `UNDERSTAND ──▶ PLAN ──▶ MODIFY ──▶ TEST ──▶ VERIFY ──▶ REPORT`. Manifest-driven project detection (Python, Node/TS, Go, Rust), git safety (dirty-tree guards, mandatory confirmation for commits/push), ripgrep symbol & code search with automatic secret redaction (`[REDACTED]`), AST symbol extraction, targeted syntax-validated patches with rollback on failure, native test execution (pytest, npm test, cargo test, go test), and multi-category error diagnosis (`SYNTAX`, `DEPENDENCY`, `IMPORT`, `ENVIRONMENT`, `LOGIC`, `TYPE`, `PERMISSION`).
  - **Research Agent** (`agents/research/`): Multi-source synthesis across primary documentation, academic preprints, and developer forums; automated source tier classification (`PRIMARY`, `SECONDARY`, `COMMUNITY`); strict provenance tracking with verified URL citations; contradiction & consensus analysis; and structured 9-section report generation saved to centralized artifacts.
  - **Presentation Agent** (`agents/presentation/`, `tools/presentation/`): Generates genuine `.pptx` presentations using `python-pptx`, 16:9 widescreen layouts, dark-first technical color palette (`#0F172A`, `#38BDF8`, `#34D399`), structured slide layout types, overflow-proof content fitting, professional speaker notes, multi-duration pitch synthesis (30s elevator, 1m quick, 3m demo, 5m full), and 8-category technical judge Q&A anticipation.
  - **Documentation Agent** (`agents/documentation/`, `tools/documentation/`): Inspects actual codebases to generate production-grade READMEs with Mermaid architecture diagrams and installation guides, extracts FastAPI/Flask endpoints for OpenAPI/markdown API reference specs, and drafts Architecture Decision Records (ADRs).
  - **Long-Running Checkpointed Workflows** (`core/workflows/`): Stage-based durability (`research`, `requirements`, `architecture`, `implementation`, `testing`, `documentation`, `presentation`, `report`), crash recovery, state persistence via `ArtifactManager`, seamless resumption from checkpoints without re-running earlier stages, and the unified Hackathon Project Recipe (Recipe 5).
  - **Centralized Artifact Management** (`core/artifacts/`): Strict namespace isolation under `workspace/shivani-artifacts/` (`project/`, `research/`, `presentations/`, `reports/`, `checkpoints/`, `logs/`) with zero clutter in working directories.
- **Android Phone Agent & Secure Device Bridge (Phase 7)**:
  - **Native Android Companion App** (`apps/mobile/`): Built with Kotlin + Jetpack Compose, featuring a futuristic dark UI matching desktop SHIVANI across 6 dedicated screens (Home, Connection, Permissions, Activity, Devices, Settings).
  - **Secure Cryptographic Handshake**: 6-digit challenge code pairing with mutual SHA-256 HMAC token exchange; hardware-backed encryption via **Android KeyStore** (AES-256 GCM) with zero hard-coded credentials.
  - **DeviceBridge & Heartbeat Monitoring**: Keepalive ping/pong with connection drop detection (`DEVICE_DISCONNECTED`), auto-abort guards, and instant emergency stop cancellation propagation (*"Shivani stop"*).
  - **Natural Language App Resolution (`AppResolver`)**: Maps conversational English, Hindi, and Hinglish (*"phone mein Instagram kholo"*, *"phone ki settings kholo"*, *"meri photos kholo"*, *"YouTube chalao"*) to verified package identifiers with post-launch foreground verification.
  - **Minimalist Accessibility Automation (`AndroidUIObserver`)**: Enforces strict data minimization by filtering `rootInActiveWindow` to only actionable UI targets without transmitting extraneous tree data.
  - **Social Media Safety Gate**: Five-stage user approval discipline (`PREPARE ──▶ SHOW TARGET ──▶ SHOW ACTION ──▶ REQUEST APPROVAL ──▶ EXECUTE ──▶ VERIFY`) for comments, posts, and likes.
  - **Cross-Device Photo Workflow (Recipe 6)**: Searches phone photos by query/tag, transfers chosen photos securely to laptop workspace, synthesizes LinkedIn drafts, and pauses at approval gates before verified publication.
  - **Zero-Surveillance Privacy**: No continuous screen streaming, no background account scraping, on-demand notification summarization, and zero clipboard logging.
  - **141 Registered & Verified Tools**: Complete expansion of registered tools across all 7 phases with 100% test coverage (116/116 tests passing).
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
│   ├── computer/            # ComputerAgent, ScreenObserver, CurrentUIContext
│   ├── browser/             # BrowserAgent, Playwright automation & element resolution
│   ├── coding/              # CodingAgent, ProjectDetector, GitManager, PatchManager
│   ├── research/            # ResearchAgent, MultiSourceSynthesizer, ContradictionAnalyzer
│   ├── presentation/        # PresentationAgent, PPTX Generator, PitchBuilder, JudgeQA
│   ├── documentation/       # DocumentationAgent, ReadmeGenerator, ApiDocExtractor, ADR
│   └── content/             # ContentSynthesisAgent (social posts, emails, writeups)
├── apps/
│   ├── desktop/             # FastAPI backend & futuristic Web Dashboard
│   └── mobile/              # Android companion specs & bridge
├── core/
│   ├── artifacts/           # Centralized ArtifactManager (project, research, decks, checkpoints)
│   ├── orchestrator/        # State machine, executor, emergency stop, planner
│   ├── workflows/           # Composable WorkflowEngine, Checkpoints, CrossAppRecipes
│   ├── context/             # Hinglish normalizer and session context
│   ├── llm/                 # Model provider abstractions (Gemini, OpenAI, Mock)
│   ├── config.py            # Settings loader & validation
│   └── memory/              # Context & memory structures
├── integrations/
│   ├── youtube/             # YouTube search, playback & verification
│   ├── gmail/               # Gmail triage, categorizer & safe cleanup
│   ├── linkedin/            # LinkedIn draft generator & post publisher
│   ├── github/              # GitHub repo inspection, issue tracker & file ops
│   └── research/            # Multi-source web search & report generation
├── security/
│   ├── permissions/         # Risk classification & approval flow engine
│   ├── sandbox/             # Command risk classifier & path safety
│   └── audit/               # JSONL audit logger with secret redaction
├── tools/
│   ├── base.py              # BaseTool contract & ToolResult
│   ├── registry.py          # Central registry with timeout & verification (119 tools)
│   ├── coding/              # 13 Coding tools (detect, search, patch, test, error)
│   ├── presentation/        # 3 Presentation tools (build deck, pitches, judge QA)
│   ├── documentation/       # 3 Documentation tools (README, API docs, ADR)
│   ├── browser/             # 15 Browser tools (nav, click, type, tabs, summarize)
│   ├── desktop/             # OS abstraction (Windows 11), WindowManager, InputController
│   ├── computer/            # Foundation computer & process tools
│   ├── filesystem/          # List, read, write, safe delete
│   └── terminal/            # Sandboxed shell command execution
├── voice/                   # Wake word, faster-whisper STT, edge-tts TTS, pipeline
├── tests/                   # Full pytest automated test suite (104 tests passing)
├── docs/                    # Complete architecture, agents, tools & security docs
├── workspace/               # Isolated outputs and test fixtures
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
- [Device Bridge Specification](docs/DEVICE_BRIDGE.md)
- [Phone Security & Privacy Model](docs/PHONE_SECURITY.md)
- [Mobile Setup & Physical Pairing](docs/MOBILE_SETUP.md)
- [Memory Hierarchy](docs/MEMORY.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Testing & Quality Assurance](docs/TESTING.md)
- [Product Roadmap](docs/ROADMAP.md)

---

## License

MIT License. Designed and engineered for personal autonomous computer use.
