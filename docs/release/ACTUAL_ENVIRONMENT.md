# SHIVANI 1.0 — Actual Host Environment Report

*Generated: 2026-09-25T07:57:00+05:30*

## 1. Hardware Architecture
- **Host Operating System**: Microsoft Windows 11 Build 10.0.26200 (x86_64)
- **Processor**: Intel 64-bit Architecture
- **CPU Topology**: 12 Physical Cores, 14 Logical Threads
- **System Memory (RAM)**: 16.59 GB Installed / 5.91 GB Available at baseline
- **Storage**: Primary volume `C:` with 402.82 GB Total / 153.60 GB Free Disk Space
- **Graphics (GPU)**: Intel(R) Graphics (Driver 32.0.101.6874, 2.14 GB Adapter RAM)
- **Audio Inputs**: Intel(R) Smart Sound Technology for Digital Microphones (Status: OK)
- **Audio Outputs**: Realtek High Definition Audio (Status: OK)

---

## 2. Software & Tooling Environment
- **Python Runtime**: CPython 3.12.13 (Managed by Astral `uv` at `C:\Users\shiva\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe`)
- **Virtual Environment**: `.venv` with site-packages at `C:\Users\Project\Jarvis\.venv`
- **Node.js**: `v20.x` (`C:\Program Files\nodejs\node.EXE`)
- **npm**: `C:\Program Files\nodejs\npm.CMD`
- **Git**: `C:\Program Files\Git\cmd\git.EXE`
- **Browsers**:
  - Google Chrome: `C:\Program Files\Google\Chrome\Application\chrome.exe` (AVAILABLE)
  - Microsoft Edge: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` (AVAILABLE)
- **Network Connectivity**: Active Internet (HTTPS to external domains verified)

---

## 3. Peripheral & Tooling Status
- **Android ADB**: NOT FOUND on PATH (`adb.exe` not detected)
- **Local LLM Engine (Ollama)**: NOT FOUND on PATH (No local daemon detected)
- **Tesseract OCR Binary**: NOT FOUND on PATH (Local Windows Media OCR / PyAutoGUI fallback active)
- **FFmpeg Binary**: NOT FOUND on PATH (Python wave/audio fallback active)

---

## 4. Privacy & Secret Boundary Verification
- Zero plaintext API tokens or user credentials exist in configuration dumps or runtime manifests.
- Secret vault is securely encrypted using native Windows DPAPI in `%APPDATA%\Shivani\data\vault.enc`.
