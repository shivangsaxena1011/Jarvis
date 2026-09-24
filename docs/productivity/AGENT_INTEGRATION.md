# Cross-Agent Workflows & Tool Integration

## 1. Project Agent Architecture
`agents/project/project_agent.py` implements the `ProjectAgent`, extending `BaseAgent`.

### Responsibilities
1. **Decomposition**: Accepts high-level project goals and generates milestone/task proposals.
2. **Context Provider**: Supplies active project parameters (codebase root, tech stack, conventions) to downstream agents.
3. **Cross-Agent Dispatch**:
   - Dispatches research questions to `ResearchAgent`.
   - Dispatches implementation tasks to `CodingAgent`.
   - Dispatches reports and briefing slides to `PresentationAgent`.
4. **Deliverable Verification**: Collects generated artifacts and runs them through `TaskCompletionGate`.

---

## 2. Productivity Tools Registered in Orchestrator
Total registered system tools increased from 168 to 173:
1. `task.create`: Creates a personal task with priority, due date, duration, and project link.
2. `task.list`: Queries personal tasks with status or project filters.
3. `task.complete`: Passes completion through verification gate with artifact/test/manual proof.
4. `project.context`: Fetches active project context, health, and recent decisions.
5. `plan.today`: Generates a personalized daily schedule for the current date.
