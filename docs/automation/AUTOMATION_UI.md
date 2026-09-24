# SHIVANI Automation Desktop UI & User Experience

## 1. UI Architecture

The Phase 15 Automation UI is integrated into the Shivani Desktop Hub (`apps/desktop/web/`):
- Navigation Sidebar: Direct link to `⚡ Automations` view (`#view-automations`).
- Real-time Analytics Bar: Displays Total Routines, Active Routines, 24h Runs, and Overall Success Rate.
- Prompt-to-Automation Input: Natural language text bar with "Create Automation" button.
- Subtabs:
  - **Active Routines**: Grid of configured automations with trigger badges, status chips, capability tags, and inline controls (Run Now, Pause/Resume, Delete).
  - **Templates**: Pre-configured routine templates (Morning Brief, GitHub Monitor, Build Analyzer, etc.) with one-click "Use Template" instantiation.
  - **Run History**: Chronological table of past executions with run status, start time, duration, and error inspection.

---

## 2. Real-Time HUD & System Tray Notifications

- Quiet hours protection: Suppresses audible chimes between 22:00 and 07:00 while queuing visual badges.
- Interactive approval cards: When a high-risk step requires authorization, a floating HUD toast appears with **Approve** and **Deny** buttons.
- Failure banners: Clear diagnostics indicating exact step failure reason without exposing sensitive credential data.
