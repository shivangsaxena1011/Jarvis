# SHIVANI — Cross-Application Workflow Engine

## Workflow Engine (`core/workflows/engine.py`)

The Workflow Engine manages complex multi-step routines spanning multiple agents (`system`, `computer`, `browser`, `content`, `github`, `gmail`, `linkedin`).

### Key Properties & Safety Contracts

1. **Sequential Chaining & Dynamic Variables**:
   Steps execute sequentially. Outputs from earlier steps are placed into the shared `context_data` and can be referenced via `{placeholder}` syntax in subsequent step inputs (e.g. `{draft_id}`, `{project_name}`, `{summary_text}`).

2. **Approval Pausing & Non-destructive Resumption**:
   When a step requires human confirmation (e.g. `RiskLevel.CRITICAL`, social publishing, batch deletion, or `requires_approval=True`):
   - The workflow pauses in `WAITING_FOR_APPROVAL` state.
   - An `ApprovalRequest` is registered in `PermissionEngine`.
   - The exact state, step index, and context data are preserved.
   - On approval (`resume_workflow(id, approved=True)`), execution resumes precisely from the paused step without re-running earlier steps.
   - On rejection (`resume_workflow(id, approved=False)`), the workflow transitions cleanly to `CANCELLED`.

3. **Failure Diagnostics**:
   If any step fails, the engine captures system diagnostics (active window, environmental snapshots) and publishes a `TOOL_FAILED` event before halting safely.

## Master Recipes (`core/workflows/cross_app_recipes.py`)

### 1. Local Project to LinkedIn Showcase
```python
create_project_to_linkedin_workflow(project_name: str, image_path: Optional[str] = None)
```
- Step 1: `project.find` — Discovers project metadata and README summary.
- Step 2: `content.generate_linkedin_post` — Generates high-impact draft.
- Step 3: `linkedin.prepare_post` — Prepares post in `DRAFT` state.
- Step 4 (Approval Gate): `linkedin.publish_post` — Waits for user authorization before posting.

### 2. Gmail Triage & Two-Stage Cleanup
```python
create_gmail_triage_workflow(max_age_days: int = 30)
```
- Step 1: `gmail.summarize` — Scans inbox and generates categorized summary.
- Step 2: `gmail.cleanup_proposal` — Analyzes newsletters/promotions and builds cleanup proposal.
- Step 3 (Approval Gate): `gmail.execute_cleanup` — Requires user approval before archiving.

### 3. Multi-Source Autonomous Research
```python
create_research_workflow(topic: str, output_dir: Optional[str] = None)
```
- Step 1: `research.search` — Queries web and literature sources.
- Step 2: `research.synthesize` — Synthesizes findings with provenance and citations.
- Step 3: `research.save` — Exports `report.md`, `sources.json`, and `summary.json`.

### 4. GitHub Project Inspection & Safe Run
```python
create_github_inspect_and_run_workflow(repo_name_or_query: str)
```
- Step 1: `github.inspect_repository` — Inspects repo structure.
- Step 2: `github.inspect_runnable` — Analyzes entry point and package manager.
- Step 3 (Approval Gate): `terminal.execute` — Runs project command with safety gate.
