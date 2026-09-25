# SHIVANI 1.0 — MASTER ARCHITECTURE SPECIFICATION

```
                         USER
                          │
             ┌────────────┴────────────┐
             │                         │
          VOICE                      UI (Desktop / Web / Mobile)
             │                         │
             └────────────┬────────────┘
                          │
                    SHIVANI CORE
                          │
                ┌─────────┴─────────┐
                │                   │
          CONTEXT ENGINE       SECURITY PERIMETER
                │                   │
                └─────────┬─────────┘
                          │
                  MASTER ORCHESTRATOR
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
      PLANNER           MEMORY          KNOWLEDGE OS
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                    MODEL ROUTER
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
     LOCAL              CLOUD           SPECIALIZED
  (Ollama/llama)    (Frontier APIs)     (Whisper/Piper/OCR)
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                    AGENT REGISTRY
                          │
       ┌──────────┬───────┼────────┬──────────┐
       │          │       │        │          │
   Computer    Browser   Coding  Research  Productivity
       │          │       │        │          │
       └──────────┴───────┼────────┴──────────┘
                          │
                     SKILL SYSTEM
                          │
                     TOOL SYSTEM
                          │
                  PERMISSION ENGINE
                          │
                     EXECUTION
                          │
                    VERIFICATION
                          │
                  RECOVERY ENGINE
                          │
                  CROSS-DEVICE BUS
                     │          │
                 WINDOWS PC   ANDROID PHONE
```

---

## 1. End-to-End Processing Trajectory

```
User (Voice / Text / Image / File)
 ↓
Shivani UI (FastAPI Server, Desktop HUD, WebSocket/SSE)
 ↓
Core Runtime (State Machine, Session Context, Audio State)
 ↓
Master Orchestrator (`core/orchestrator/orchestrator.py`)
 ↓
Context Engine (Milestone compression, token budgeting)
 ↓
Task Planner (`TaskPlanner`, `TaskDecomposer`, DAGs)
 ↓
Memory / Knowledge (`MemoryManager`, `KnowledgeOS`)
 ↓
Model Router (`ModelRouter`, Deterministic Fast-Paths)
 ↓
Agent Registry (`AgentRegistry`, subagents)
 ↓
Skill Registry (`SkillRegistry`, verified plugins)
 ↓
Permission Engine (`PermissionEngine`, scoped approvals)
 ↓
Tool Execution (Sandboxed OS Adapter, Browser, Device Bridge)
 ↓
Verification (`VisualQA`, state diff, evidence validation)
 ↓
Recovery (`RecoveryEngine`, checkpoints, self-repair)
 ↓
User Response (Natural text, UI artifact, Piper-TTS audio)
```

---

## 2. Fundamental System Invariants

### Invariant 1: Observe → Understand → Plan → Authorize → Act → Verify → Report
No state mutation occurs without explicit verification and evidence collection. An agent can never report "Done" unless the observed world state confirms completion.

### Invariant 2: Models Are Not Authorities
Large Language Models are probabilistic reasoning engines, not execution authorities. Model proposals must pass structural validation, injection filtering, permission checks, and user authorization prior to execution.

### Invariant 3: Zero-Cloud Privacy Perimeter
Cryptographic keys, passwords, bearer tokens, financial records, and files marked `CRITICAL` or `SENSITIVE` are never transmitted to external cloud providers.

### Invariant 4: Truthful Degradation
When offline or air-gapped, Shivani remains 100% operational on local tools, files, and models, but never hallucinates or fabricates real-time external data.

---

## 3. Subsystem Breakdown

### A. Core Runtime & Orchestrator
- **State Machine**: `PENDING` ➔ `PLANNING` ➔ `WAITING_FOR_PERMISSION` ➔ `EXECUTING` ➔ `VERIFYING` ➔ `RECOVERING` ➔ `COMPLETED` (exits: `FAILED`, `CANCELLED`, `PAUSED`, `BLOCKED`).
- **Emergency Controller**: Global kill-switch with near-immediate propagation across all subprocesses, browser tabs, and network relays.
- **Task Watchdog**: Detects infinite loops, repeated tool failures, stalled browsers, or unresponsive device handoffs.

### B. Intelligent Model Routing
- **Deterministic Fast Paths**: Zero-latency, exact evaluation for math arithmetic and standard OS window commands.
- **Local Models**: 3B (`phi3:mini`) and 7B/8B (`llama3.1:8b`, `qwen2.5-coder:7b`) running on host RAM/VRAM via Ollama.
- **Frontier Cloud**: Gemini, Claude, and GPT-4o for complex multi-file refactoring and academic research synthesis.

### C. Cross-Device Continuity
- **Mesh Topology**: Windows PC (Primary node) and Android Companion (Secondary node) authenticated via 6-digit PIN and SAS phrase.
- **Handoff Engine**: Minimal context serialization allowing tasks initiated on PC to resume on mobile and vice-versa.
- **Ambient Intelligence**: Contextual presence sensing with zero surveillance overhead.

### D. Memory & Knowledge OS
- **Personal Memory**: Semantic user preference learning, episodic history, and explicit forgetting via SQLite.
- **Knowledge OS**: Local hybrid vector search, entity relationship graphs, and automated document indexing.
