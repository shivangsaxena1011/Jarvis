# Voice & Conversational Control — SHIVANI (Phase 2)

SHIVANI features a voice-first conversational interface supporting English, Hindi, and mixed Hinglish instructions.

---

## 1. End-to-End Voice Architecture

```
[User Speech]
      │
      ▼
[Audio State: LISTENING]
      │
      ▼
[Local Wake Word Detection: "Shivani"]
      │
      ▼
[Audio Capture & VAD Silence Trimming]
      │
      ▼
[Audio State: PROCESSING]
      │
      ▼
[Speech-to-Text: faster-whisper / Whisper]
      │
      ├── High Confidence (>= 0.65) ────────┐
      │                                      ▼
      │                     [Conversational Context Manager]
      │                     (Multi-Turn & Follow-Up Resolution)
      │                                      │
      │                                      ▼
      │                             [Agent Orchestrator]
      │                       (OBSERVE -> PLAN -> ACT -> VERIFY)
      │                                      │
      │                                      ▼
      │                             [Task Result Formatter]
      │
      └── Low Confidence (< 0.65)
              │
              ▼
    [Generate Clarification: "क्या आपने कहा कि..."]
              │
              ▼
[Audio State: SPEAKING]
      │
      ▼
[Text-to-Speech: Edge-TTS / pyttsx3]
      │
      ├── Interrupt Signal ("Shivani stop") ──► [Immediate Cutoff (<50ms)]
      │
      ▼
[Audio State: IDLE]
```

---

## 2. Audio State Machine

The audio engine transitions through five states:
- `IDLE`: Microphone monitoring or waiting for wake word / PTT trigger.
- `LISTENING`: Actively streaming or capturing user speech chunks.
- `PROCESSING`: Transcribing speech via STT and formulating task plan.
- `SPEAKING`: Playing synthesized neural speech response.
- `ERROR`: Capturing and displaying speech or audio hardware exceptions.

The state is synchronized in real time with the Desktop Web Dashboard status badge and glowing Core Orb.

---

## 3. Wake Word Detection
- **Trigger Phrase**: `"Shivani"` (with phonetic variants: *"shiwani"*, *"shivanee"*, *"suno shivani"*).
- **Processing**: 100% local processing using acoustic energy thresholding and fuzzy phonetic matching. Ambient room audio is never continuously uploaded to remote clouds.

---

## 4. Speech-to-Text (STT) Engine
- **Engine**: `faster-whisper` (CTranslate2 + ONNX runtime).
- **Models**:
  - `tiny`: Lightweight, ultra-fast for CPU inference (default).
  - `base` / `small`: Enhanced accuracy for noisy environments.
- **Multilingual Support**: English, Hindi, and Hinglish.
- **Anti-Hallucination Guardrail**:
  If transcription confidence falls below `CONFIDENCE_THRESHOLD` (default 0.65), SHIVANI does not execute high-risk operations. Instead, it asks for clarification:
  *"क्या आपने कहा कि [Action] करना है?"*

---

## 5. Text-to-Speech (TTS) & Immediate Speech Interruption
- **Default Voice**: `hi-IN-SwaraNeural` (Natural, feminine Hindi/English neural voice).
- **Alternative Voices**:
  - `en-IN-NeerjaNeural`: Indian English.
  - `en-US-AriaNeural`: American English.
- **Offline Fallback**: `pyttsx3` with Windows SAPI5 female voice.
- **Speech Interruption**:
  Users can interrupt SHIVANI at any time by saying *"Shivani stop"* or clicking **Stop**. The audio playback process is halted within <50ms.

---

## 6. Multi-Turn Conversational Context

SHIVANI preserves conversational state across sequential turns:

| Turn | User Spoken Input | Context Resolution & Action | SHIVANI Spoken Response |
|---|---|---|---|
| 1 | *"Shivani, Chrome kholo."* | Opens Chrome browser. Sets `active_app=chrome`. | *"Done."* |
| 2 | *"YouTube kholo."* | Resolves to: *Open YouTube in Chrome*. Sets `active_domain=youtube`. | *"Sure."* |
| 3 | *"Arijit Singh search karo."* | Resolves to: *In YouTube, search Arijit Singh*. | *"Done."* |
| 4 | *"Isko band karo."* | Resolves deictic reference: *Close Chrome*. | *"Done."* |

---

## 7. Push-to-Talk (PTT) & Web Dashboard Usage

The Desktop Web Dashboard includes a built-in browser audio recorder:
1. Open `http://127.0.0.1:8000`.
2. Click **[Start Listening]** to capture audio via your microphone.
3. Speak your command naturally (e.g. *"Shivani, YouTube kholo"*).
4. Click **[Listening... (Click to Send)]**.
5. SHIVANI transcribes the query, executes the verified task, and plays back the spoken response directly through your speakers or browser.

---

## 8. Configuration (`.env`)

```env
VOICE_ENABLED=true
WAKE_WORD=Shivani
STT_PROVIDER=whisper
STT_MODEL=tiny
TTS_PROVIDER=edge_tts
TTS_VOICE=hi-IN-SwaraNeural
TTS_RATE=+0%
CONFIDENCE_THRESHOLD=0.65
```

---

## 9. Troubleshooting

- **Microphone access denied in browser**: Ensure the browser has granted microphone permissions for `http://localhost:8000`.
- **Whisper CPU performance**: Use `STT_MODEL=tiny` for sub-second CPU transcription.
- **Audio playback blocked**: Modern browsers require user interaction before autoplaying audio; clicking the PTT button provides this authorization.
