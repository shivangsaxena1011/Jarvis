# SHIVANI Assistant State Machine Specification

## 1. Overview
The Assistant State Machine in `apps/desktop/server.py` (`assistant_state_mgr`) is the single source of truth for the entire desktop interface. Any state change triggers immediate WebSocket broadcasts to the Floating HUD, Spotlight Command Bar, Main Dashboard, and System Tray icon.

```
       +-------------------------------------------------------------+
       |                                                             |
       v                                                             |
    [ IDLE ] <----------+                                            |
       |                |                                            |
 (Wake Word / PTT)      |                                            |
       v                |                                            |
  [ LISTENING ]         |                                            |
       |                |                                            |
 (Audio Complete)       |                                            |
       v                |                                            |
 [ TRANSCRIBING ]       |                                            |
       |                |                                            |
 (Intent Extraction)    |                                            |
       v                |                                            |
[ UNDERSTANDING ]       |                                            |
       |                |                                            |
  (DAG Decompose)       |                                            |
       v                |                                            |
   [ PLANNING ]         |                                            |
       |                |                                            |
       +------- (Needs Human Approval?) ------+                      |
       | NO                                  YES                     |
       v                                      v                      |
  [ EXECUTING ]                      [ WAITING_FOR_PERMISSION ]      |
       |                                      |                      |
       |                             (User Approved?)                |
       |                             /              \                |
       |                         (YES)              (NO)             |
       |                          /                    \             |
       +<------------------------+                      v            |
       |                                           [ CANCELLED ] ----+
       v
  [ VERIFYING ]
       |
       +--------- (Pass / Fail / Recover) --------+
       |                                          |
    (PASS)                                     (FAIL)
       v                                          v
  [ SPEAKING ]                              [ RECOVERING ]
       |                                          |
       v                                          +----+
  [ COMPLETED ]                                        |
       |                                      (Recovery Failed)
       +-------------------------------------> [ FAILED ]
```

---

## 2. Complete State Definitions

| State | HUD Orb Visual | Tray Icon | Description |
| :--- | :--- | :--- | :--- |
| `IDLE` | Calm Cyan Glow | `READY` (Cyan) | Assistant is resting, ready for voice or keyboard input. |
| `LISTENING` | Pulsing Green Wave | `LISTENING` (Green)| Microphone is recording user audio stream. |
| `TRANSCRIBING` | Amber Spinner | `PROCESSING` (Amber)| Whisper local STT is transcribing speech to text. |
| `UNDERSTANDING`| Indigo Pulse | `PROCESSING` (Amber)| Intent parsing and entity extraction in progress. |
| `PLANNING` | Dual Purple Orbit Rings| `PROCESSING` (Amber)| Decomposing user goal into executable Task DAG. |
| `WAITING_FOR_PERMISSION`| Amber Double Blink | `APPROVAL` (Amber) | Execution paused pending user confirmation of sensitive/high-risk action. |
| `EXECUTING` | Active Cyan Ripple | `WORKING` (Cyan) | Step tools executing (browser, bash, file, desktop). |
| `VERIFYING` | Subtle Blue Pulse | `WORKING` (Cyan) | Validating step output against expected postconditions. |
| `RECOVERING` | Orange Ripple | `WORKING` (Orange)| Self-correcting step failure or reloading checkpoint. |
| `SPEAKING` | Radiant Violet Wave | `READY` (Cyan) | TTS pipeline synthesizing and playing audio response. |
| `COMPLETED` | Solid Emerald Flash| `READY` (Green) | Task DAG successfully executed and artifacts saved. |
| `FAILED` | Red Shake | `OFFLINE` (Red) | Task encountered unrecoverable error. |
| `CANCELLED` | Red Static | `PAUSED` (Gray) | Execution aborted via Emergency Stop or User Cancel. |
| `OFFLINE` | Gray Hollow Ring | `OFFLINE` (Gray) | Core engine disconnected or health check degraded. |

---

## 3. Special Operational Overrides

### 3.1 Privacy Mode
- When engaged via HUD, Command Bar, or Tray, the system:
  1. Closes active microphone streams and rejects wake-word triggers.
  2. Blinds screen capture and camera capture tools.
  3. Displays a persistent `[PRIVACY ACTIVE]` badge across the UI.

### 3.2 Security Lock
- When the assistant is locked:
  1. All new task submissions via REST or WebSocket return `HTTP 423 Locked`.
  2. The UI renders the full-screen Security Lock Overlay.
  3. Unlocking requires entering the user's secure PIN (verified via DPAPI/Argon2id vault).
