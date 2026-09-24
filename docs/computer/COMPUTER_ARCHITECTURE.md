# SHIVANI AI — Phase 17: Computer Autonomy Architecture

## 1. System Philosophy & Closed-Loop Autonomy

Traditional desktop automation relies on macro-recorders or open-loop coordinate clicks with hardcoded sleep intervals:
```text
CLICK -> SLEEP -> CLICK -> SLEEP -> HOPE
```

Shivani's **Computer Autonomy Agent (Phase 17)** replaces this with a genuine **closed-loop computer-use agent**:
```text
OBSERVE
   ↓
UNDERSTAND
   ↓
 PLAN
   ↓
  ACT
   ↓
OBSERVE AGAIN
   ↓
 VERIFY
   ↓
RECOVER / REPLAN
   ↓
CONTINUE
   ↓
 REPORT
```

---

## 2. High-Level Architecture Diagram

```text
                               ┌────────────────────────────────────────────────────────┐
                               │                    MASTER ORCHESTRATOR                 │
                               │                (core/orchestrator/orchestrator.py)     │
                               └───────────────────────┬────────────────────────────────┘
                                                       │
                                                       ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       COMPUTER AUTONOMY AGENT                                         │
│                                      (core/computer/agent.py)                                         │
├───────────────────┬───────────────────┬───────────────────┬───────────────────┬───────────────────────┤
│ Observation Engine│ Semantic Graph    │ Visual Grounding  │ Expectation Engine│ Execution Engine      │
│ (UIA + OCR +      │ (Hierarchical UI  │ (Multi-source     │ (Pre/Post diff,   │ (Closed-loop observe/ │
│  Vision + Window) │  Spatial Engine)  │  Confidence Gate) │  Expected states) │  act/verify cycle)    │
├───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────────┤
│ Recovery Engine   │ Checkpoint Engine │ Resource Lock     │ Terminal Engine   │ App Adapter Registry  │
│ (Loop detect,     │ (Safe resume,     │ (Priority &       │ (Safety filter,   │ (VS Code, Explorer,   │
│  Dynamic replan)  │  Rollback state)  │  Takeover)        │  Output parser)   │  Office, Browsers)    │
└───────────────────┴───────────────────┴───────────────────┴───────────────────┴───────────────────────┘
                                                       │
                        ┌──────────────────────────────┴──────────────────────────────┐
                        ▼                                                             ▼
           ┌──────────────────────────┐                                  ┌──────────────────────────┐
           │    SYNTHETIC GUI TEST    │                                  │    WINDOWS 11 DESKTOP    │
           │       ENVIRONMENT        │                                  │  UIA, Win32, Input, Screen│
           └──────────────────────────┘                                  └──────────────────────────┘
```

---

## 3. Core Subsystems

### 3.1 Observation Engine (`core/computer/observation_engine.py`)
Produces unified `DesktopObservation` snapshots fusing:
1. Win32 foreground and window enumeration.
2. Windows UI Automation (UIA) tree inspection.
3. Multi-monitor display geometry and scale factors.
4. Optical Character Recognition (OCR) text detection.
5. Visual bounding boxes and layout detection.
6. System clipboard inspection with automated privacy masking for tokens and secrets.

### 3.2 UI Semantic Graph (`core/computer/semantic_graph.py`)
Builds a functional hierarchy:
`Window -> Sections (Toolbar, Sidebar, Content, Dialog, Status) -> Controls (Buttons, Inputs)`.
Enables high-level instructions like: *"Click Save in the Toolbar"* rather than low-level pixel coordinates.

### 3.3 Visual Grounding & Spatial Reasoning (`core/computer/visual_grounding.py`, `spatial_engine.py`)
Resolves natural language queries by evaluating spatial relationships (`above`, `below`, `left_of`, `right_of`, `inside`, `contains`, `near`, `between`) and computing multi-source confidence scores. Rejects ambiguous queries when multiple candidates match equally.

### 3.4 Expectation & Verification Engine (`core/computer/expectation_engine.py`)
Defines expected outcomes prior to action dispatch and verifies state transitions by computing structural differences (`StateDifference`) between pre-action and post-action observations.

### 3.5 Checkpointing & Safe Resume (`core/computer/checkpoint_engine.py`)
Persists step-by-step task checkpoints (`TaskCheckpoint`). On resumption, inspects current observed reality to skip already-satisfied steps rather than blindly replaying past actions.

### 3.6 Resource Locking & Priority Hierarchy (`core/computer/resource_lock.py`)
Manages exclusive locks across `Desktop`, `Browser`, `Terminal`, `VSCode`, and `Clipboard` following a strict priority ladder:
1. `EMERGENCY_STOP` (100)
2. `DIRECT_USER_COMMAND` (80)
3. `USER_APPROVED_TASK` (60)
4. `INTERACTIVE_AUTOMATION` (40)
5. `SCHEDULED_AUTOMATION` (20)
6. `BACKGROUND_AUTOMATION` (10)
