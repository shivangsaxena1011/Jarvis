# Desktop UI & Productivity Experience

## 1. Web & HUD Interface
The Phase 16 Desktop UI integrates seamlessly into the existing desktop interface (`apps/desktop/web/`).

### Features & Components
1. **Productivity Navigation Item**:
   - Sidebar icon `📅 Productivity` navigates to `view-productivity`.
2. **Key Metric Cards**:
   - **Active Tasks**: Live count of actionable `TODO` and `IN_PROGRESS` items.
   - **Active Projects**: Total running projects with health indicators (`ON_TRACK`, `AT_RISK`, `BLOCKED`).
   - **Goals Tracking**: Count of active long-term goals.
   - **Today's Focus**: Top recommended next task with its multi-factor justification.
3. **Quick Natural Language Input Bar**:
   - Allows typing queries like:
     - *"Add task prepare slide deck for project Alpha by Friday urgent"*
     - *"Create project Machine Learning Benchmark with high priority"*
   - Automatically dispatches to NLP parser and updates all relevant views.
4. **Sub-Tabs**:
   - **Tasks**: Filter by status, priority, and project; one-click completion verification gate; deletion; deferral.
   - **Projects**: Project cards with health badges, active milestone indicators, and direct codebase links.
   - **Goals**: Progress bars showing mathematically computed milestone progress.
   - **Daily Plan**: Visual schedule of time blocks with capacity warnings and user acceptance button.
