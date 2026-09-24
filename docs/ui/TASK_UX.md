# SHIVANI Task Execution & Timeline UX

## 1. Visual Task Decompositions
Complex user requests are broken down into transparent, observable Directed Acyclic Graphs (DAGs) rather than opaque black-box executions.

---

## 2. Real-time Step Timeline

Each step in the Task Timeline displays:
- **Step Number & Title**: Clear concise objective (e.g. `1. Search research sources`, `2. Synthesize findings`).
- **Assigned Tool / Agent**: Indicator of the exact subsystem in use (e.g. `browser.navigate`, `research.search`, `code.execute`).
- **Live Status Badges**:
  - `PENDING`: Gray outline pill.
  - `RUNNING`: Pulsing cyan pill with active spinner.
  - `COMPLETED`: Emerald checkmark badge with execution duration (e.g. `240ms`).
  - `FAILED`: Red alert badge with collapsible error stack and auto-recovery status.
- **Collapsible Reasoning Logs**: Users can click any step to expand the underlying LLM thought rationale, intermediate outputs, and tool call arguments.

---

## 3. Conversational Task Cards

In the main conversation stream, every task generates an embedded card that updates in real-time:
```
+-------------------------------------------------------------------------+
| [TASK] Research Multimodal Vision Models                                |
| ID: task-9081  | Status: EXECUTING (Step 2 of 3)                        |
|                                                                         |
| Progress: [████████████████████████░░░░░░░░░░░░] 66%                    |
|                                                                         |
| > Step 1: Query arXiv & Google Scholar           [✓ COMPLETED 1.2s]     |
| > Step 2: Synthesize findings & citations        [● RUNNING 0.8s]       |
| > Step 3: Generate Markdown Research Report      [○ PENDING]            |
|                                                                         |
| [View Detailed Timeline]  [Pause Workflow]  [Cancel Task]               |
+-------------------------------------------------------------------------+
```

---

## 4. Multi-Agent Collaboration Visualization

When a master task triggers specialized subagents (e.g. Research Agent + Coding Agent + Presentation Agent):
- The timeline groups steps by agent badge (`[RESEARCH]`, `[CODER]`, `[DESIGN]`).
- Resource locks and cross-agent message handoffs are displayed as connector threads between step cards.
