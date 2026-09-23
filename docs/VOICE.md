# Voice Processing Layer — SHIVANI

SHIVANI is designed as a **voice-first** agent, accepting spoken natural language in both English and Hindi / Hinglish.

---

## Architecture

```
Microphone
    │
    ▼
Wake Word Detector ("Shivani")
    │
    ▼
Speech-to-Text (STT Engine)
    │
    ▼
Hinglish Normalizer & Context
    │
    ▼
Orchestrator Pipeline
    │
    ▼
Text-to-Speech (TTS Engine)
    │
    ▼
Audio Speaker Output
```

---

## 1. Wake Word Detection
- **Target Phrase**: `"Shivani"`
- **Provider Interface**: `WakeWordDetector`
- **Supported Backends**:
  - `openWakeWord`: Efficient local neural wake word detector.
  - Mock detector for automated testing and headless servers.

---

## 2. Speech-to-Text (STT)
- **Provider Interface**: `STTProvider`
- **Supported Backends**:
  - `faster-whisper`: Optimized Whisper model running locally on CPU/CUDA.
  - Whisper-compatible HTTP endpoints.

---

## 3. Text-to-Speech (TTS)
- **Provider Interface**: `TTSProvider`
- **Voice Style**: Calm, concise, professional female voice.
- **Supported Backends**:
  - `Edge TTS`: High-quality natural neural voice synthesis (multilingual English/Hindi voices such as `en-IN-NeerjaNeural` or `hi-IN-SwaraNeural`).
  - `Piper`: Fast offline neural TTS.

---

## 4. Voice Response Guidelines
- Keep conversational turnarounds brief (*"Sure"*, *"On it"*, *"Done"*).
- Never narrate raw internal thoughts or chain-of-thought tokens over audio.
- When an action is completed, state only the verified outcome: *"Done. The screenshot has been saved."*
