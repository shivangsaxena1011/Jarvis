# Productivity OS Security, Safeguards & Boundaries

## 1. Core Principles

### 1.1 Decision Assistance, Not Autonomy
Shivani operates strictly as a decision-support system:
- **No Silent Commitments**: Shivani will never automatically accept meetings, delete projects, or alter deadlines without explicit user review.
- **Transparent Justification**: Every automated priority, schedule, and recommendation exposes its exact calculation criteria (`why_surfaced`).

### 1.2 Verification Over Assumption (Completion Gate)
A major vulnerability in autonomous agent design is "hallucinated completion"—where an agent marks a task complete because it believes it succeeded.
- `TaskCompletionGate` forbids setting `status = COMPLETED` unless:
  1. A verified deliverable artifact exists on disk.
  2. An automated test suite exits with code 0.
  3. The user explicitly confirms manual completion.

### 1.3 Personal Data Isolation & No Psychological Inferences
- Productivity metrics (focus session durations, completed task counts, velocity) are strictly operational engineering statistics.
- **Strict Prohibition**: The system is architecturally forbidden from making psychological, emotional, behavioral, or medical inferences about the user.
- Task descriptions and project notes are never leaked across tenant or user boundaries.

### 1.4 Code Injection Prevention
- All dependency, deadline, and planning calculations are executed using typed Python logic and Pydantic validation.
- Zero usage of `eval()`, `exec()`, or dynamic shell strings.

### 1.5 Cross-Project Boundary Isolation
- File modifications requested during project execution are validated against the active project's declared root.
- Path traversal outside the codebase root requires explicit interactive confirmation.
