# SHIVANI Privacy, Security & Lock Screen UX

## 1. Zero-Trust Privacy Guarantees
SHIVANI provides clear, visual physical and digital controls over data capture and execution:

### 1.1 One-Click Privacy Blinder
- Available on the Floating HUD, Spotlight Command Bar, and Windows System Tray.
- **Microphone Blinder**: Hard-mutes all microphone audio inputs and halts wake-word listener threads.
- **Vision Blinder**: Temporarily injects an opaque privacy overlay or returns blank bitmaps for all screenshot/screen capture tool calls.
- **Visual Feedback**: The interface glows with an unmistakable amber/red warning shield and displays `[PRIVACY MODE: ACTIVE]`.

---

## 2. Workstation Security Lock Screen

For unattended environments, the user can lock the assistant:
- Shortcut: `Ctrl + L` (in-app) or via System Tray -> Lock Assistant.
- **Enforcement**:
  - The main dashboard replaces all active panels with a secure PIN entry overlay.
  - Any task submitted via REST, WebSocket, or Voice receives `HTTP 423 Locked`.
  - Background tasks requiring approval remain suspended in a safe, non-executing state.
- **Unlocking**:
  - The user enters their 4-digit PIN (default `1234` or configured hash).
  - Valid PIN restores the active session state without data loss.

---

## 3. Emergency Stop Subsystem (`Ctrl + Shift + S`)

The Emergency Stop button is globally accessible across all views:
1. Immediately cancels all running asyncio tasks and subagents.
2. Halts any pending browser automation or Playwright sessions.
3. Kills any spawned subprocesses or terminal executions.
4. Drops active Android device bridge commands.
5. Transitions assistant state to `CANCELLED` and displays a red emergency alert banner.
