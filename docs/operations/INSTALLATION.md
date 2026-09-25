# SHIVANI 1.0 Installation Guide

## 1. Prerequisites
- **Operating System**: Windows 10/11 64-bit (Build 19041+ recommended).
- **Python**: Python 3.12+ 64-bit (or Astral `uv`).
- **Memory**: Minimum 8 GB RAM (16 GB+ recommended for local LLM inference).
- **Storage**: Minimum 500 MB free space for core runtime; 10 GB+ if running local LLMs via Ollama.

---

## 2. Automated Installation (Recommended)
Run the automated installation script from an elevated or standard PowerShell terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install.ps1
```

The script will:
1. Initialize the application directory structure at `%APPDATA%\Shivani`.
2. Generate the global CLI shim launcher (`%APPDATA%\Shivani\bin\shivani.cmd`).
3. Add `%APPDATA%\Shivani\bin` to your User `PATH`.
4. Create the default production configuration (`config\shivani_config.json`).
5. Execute the system diagnostic doctor check.

---

## 3. Manual Installation
If installing manually:

```powershell
# 1. Clone repository
git clone https://github.com/your-org/shivani.git
cd shivani

# 2. Create virtual environment
uv venv
.\.venv\Scripts\activate

# 3. Install dependencies in editable mode
uv pip install -e .

# 4. Run system diagnostics
uv run python cli/main.py doctor
```

---

## 4. Starting the Desktop Assistant
To launch the FastAPI desktop server and HUD:

```powershell
shivani start
# or via direct Python
uv run python cli/main.py start
```

Access the desktop interface at `http://localhost:8000`.
