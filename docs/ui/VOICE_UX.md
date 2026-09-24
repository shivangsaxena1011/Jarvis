# SHIVANI Voice Experience & Interaction Guidelines

## 1. Multi-Modal Voice Architecture
SHIVANI provides a natural, voice-first interaction experience supported by three complementary input triggers:
1. **Always-on Wake-Word Detection**: Porcupine / openWakeWord engine tuned to the customizable trigger `"Hey Shivani"`.
2. **Push-to-Talk (PTT)**: Global keyboard shortcut (`Ctrl + Win + Space`) for noisy or shared environments.
3. **Interactive HUD Mic**: Direct one-click toggle on the Floating Assistant HUD.

---

## 2. Voice State Synchronization

```
User: "Hey Shivani"  (Wake word detected)
      │
      ▼
HUD Orb enters [LISTENING] (Emerald Green Waveform)
      │
      ▼
User speaks query: "Draft a summary of my active projects."
      │
      ▼
Silence detected / PTT released: HUD Orb transitions to [TRANSCRIBING]
      │
      ▼
Local Whisper model extracts text transcript
      │
      ▼
Transcript rendered live in Conversational Chat stream
      │
      ▼
HUD Orb moves through [UNDERSTANDING] -> [PLANNING] -> [EXECUTING]
      │
      ▼
Task finishes: TTS synthesizes concise spoken reply:
"I've summarized your 3 active projects in an artifact report."
      │
      ▼
HUD Orb enters [SPEAKING] (Violet Waveform) -> returns to [IDLE]
```

---

## 3. Barge-In Interruption Handling

- If the user speaks or presses `Ctrl + Space` / `Esc` while the assistant is speaking or executing:
  1. The TTS audio output immediately stops (`sounddevice` playback abort).
  2. The assistant transitions back to `LISTENING` or `IDLE`.
  3. No audio overlaps or garbled utterances occur.

---

## 4. Privacy Indicators

- **Hardware Mic Indicator**: The HUD mic button glows emerald green with a radiating halo whenever audio is actively recording.
- **Privacy Mode Mute**: Activating Privacy Mode immediately terminates background audio threads and displays a red slashed-mic icon.
