# SHIVANI — Coding Agent

## Overview
The Coding Agent (`agents/coding/`) enables SHIVANI to act as an autonomous software engineer.
It adheres strictly to the disciplined engineering lifecycle:

```
UNDERSTAND ──▶ PLAN ──▶ MODIFY ──▶ TEST ──▶ VERIFY ──▶ REPORT
```

The agent never directly modifies a repository without first understanding its architecture, manifest files, and test infrastructure.

---

## Core Components

1. **`ProjectDetector`** ([`agents/coding/detector.py`](file:///C:/Users/Project/Jarvis/agents/coding/detector.py)):
   - Discovers languages (Python, TypeScript, JavaScript, Rust, Go, etc.).
   - Discovers frameworks (FastAPI, Flask, Next.js, React, Express, etc.).
   - Discovers package managers (`uv`, `pip`, `npm`, `pnpm`, `yarn`, `cargo`).
   - Discovers test frameworks (`pytest`, `jest`, `vitest`, `cargo test`) and safe run commands.
   - Detects environment variable keys without exposing values.

2. **`GitManager`** ([`agents/coding/git_manager.py`](file:///C:/Users/Project/Jarvis/agents/coding/git_manager.py)):
   - Inspects git status, current branch, uncommitted working tree changes.
   - Warns on dirty working trees before applying broad modifications.
   - Checkpoint branch creation (`shivani-checkpoint-<timestamp>`).
   - Computes unified diff metrics (`files_changed`, `lines_added`, `lines_removed`).
   - Strictly requires explicit user confirmation before committing (`coding.git_commit`) or pushing (`coding.git_push`).

3. **`CodeSearch` & `CodeAnalyzer`** ([`agents/coding/analyzer.py`](file:///C:/Users/Project/Jarvis/agents/coding/analyzer.py)):
   - Fast textual and AST symbol discovery (`coding.search_code`, `coding.find_symbol`, `coding.read_code_file`).
   - Focused context assembly: gathers only relevant files and symbols for a task (max 5 files) to prevent whole-repo dumping.
   - Secret redaction: automatically replaces `API_KEY`, `TOKEN`, `PASSWORD`, `SECRET` with `[REDACTED]`.

4. **`PatchManager`** ([`agents/coding/patch_manager.py`](file:///C:/Users/Project/Jarvis/agents/coding/patch_manager.py)):
   - Targeted line and block replacements with before/after state validation.
   - Pre-write Python syntax validation (`ast.parse`) to prevent persisting syntax errors.
   - Unified diff tracking.

5. **`TestRunner` & `BuildRunner`** ([`agents/coding/test_runner.py`](file:///C:/Users/Project/Jarvis/agents/coding/test_runner.py)):
   - Sandboxed execution of native test and build commands (`coding.run_tests`, `coding.run_build`).
   - Captures stdout, stderr, execution times, passed/failed test counts, and specific test failure names.

6. **`ErrorAnalyzer`** ([`agents/coding/error_analyzer.py`](file:///C:/Users/Project/Jarvis/agents/coding/error_analyzer.py)):
   - Classifies failures into 8 categories:
     - `SYNTAX`: SyntaxError, IndentationError, invalid tokens.
     - `DEPENDENCY`: ModuleNotFoundError, missing npm packages; suggests package installation.
     - `TYPE_ERROR`: TypeError, AttributeError, TypeScript errors.
     - `RUNTIME`: Unhandled exceptions, KeyError, IndexError.
     - `CONFIGURATION`: Missing files, missing env vars.
     - `NETWORK`: Connection refused, timeout, DNS resolution.
     - `DATABASE`: Connection errors, missing schemas or migrations.
     - `ENVIRONMENT`: Permission errors, compiler absence.
   - Formulates targeted remediation and identifies missing dependencies.

---

## Registered Tools
- `coding.inspect_project`: Inspects project directory and detects stack.
- `coding.search_code`: Scans codebase for keywords or tokens.
- `coding.find_symbol`: Locates class/function definitions using AST.
- `coding.read_code_file`: Reads files with secret masking and line slicing.
- `coding.apply_patch`: Applies targeted replacements with syntax check (requires confirmation).
- `coding.create_file`: Safely creates new files (requires confirmation).
- `coding.run_tests`: Executes native test suite and captures results.
- `coding.run_build`: Executes build or typecheck pipelines.
- `coding.analyze_error`: Diagnoses error logs and prescribes solutions.
- `coding.git_status`: Inspects working tree cleanliness and current branch.
- `coding.git_diff`: Computes unified diff of uncommitted changes.
- `coding.git_commit`: Commits changes (strictly gated behind user confirmation).
- `coding.git_push`: Pushes changes to remote (strictly gated behind user confirmation).
