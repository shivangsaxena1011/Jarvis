# Project Context & Cross-Project Boundary Isolation

## 1. Context Switching & Memory Grounding
Shivani tracks an active project pointer in the `ContextEngine`. When switching projects:
1. **Context Load**: Restores the target project's metadata, root codebase directory, open blockers, recent architectural decisions, and current milestone.
2. **Memory Provenance**: Memories and retrieval searches are grounded in the active project scope.
3. **Continuity Generation**: Generates an actionable summary on request:
   - *"Continuing project Shivani AI: Last session completed Phase 15. Next priority is Phase 16 completion gate."*

---

## 2. Cross-Project File Boundary Safety
Autonomous computer-use and coding agents must respect sandbox boundaries:

1. **Path Boundary Validation**:
   - `ContextEngine.validate_file_path_for_project(project_id, file_path)` ensures the target file resides strictly within the declared `codebase_path`.
2. **Cross-Project Warning & Block**:
   - If an agent or tool attempts to edit or delete files belonging to `Project B` while active in `Project A`, the execution gate intercepts the action:
     > *"Security Boundary Violation: File 'C:\Projects\Beta\config.yaml' is outside active project 'Alpha'. Cross-project file modification requires explicit confirmation."*
3. **Stale Project Safeguard**:
   - Projects inactive for >30 days trigger a stale warning to prevent unintentional edits to deprecated branches or repositories.
