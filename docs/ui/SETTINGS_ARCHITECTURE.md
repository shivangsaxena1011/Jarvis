# SHIVANI Settings & Persona Architecture

## 1. Overview
The Settings & Persona subsystem allows users to fine-tune the assistant's personality, communication style, voice characteristics, and system policies.

---

## 2. Configurable Persona Dimensions

- **Tone**:
  - `Professional`: Concise, formal, precise engineering terminology.
  - `Friendly` (Default): Warm, encouraging, empathetic, conversational.
  - `Direct`: Terse, bullet-point focused, minimal conversational filler.
- **Verbosity**:
  - `Terse`: Minimal output, status codes, and direct links.
  - `Balanced` (Default): Clear summary followed by key highlights.
  - `Detailed`: Comprehensive rationale, step-by-step reasoning, and diagnostic details.
- **Proactive Suggestions**:
  - Toggles whether the assistant autonomously offers follow-up actions (e.g. suggesting calendar events after reading an email).

---

## 3. Persistence & Synchronization

- Settings modified in the Desktop UI are persisted via `POST /api/settings` and stored in the user's local configuration directory (`~/.config/Shivani/settings.json` or Windows `%APPDATA%/Shivani`).
- Key client preferences (such as selected theme `theme-dark`/`theme-light` and HUD screen position) are cached in browser `localStorage` for immediate cold-start rendering.
