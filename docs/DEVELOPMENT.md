# Development Guide — SHIVANI

Guidelines for developing, extending, and maintaining the SHIVANI codebase.

---

## Environment Setup

1. **Python Environment**:
   Python 3.12+ is mandatory. We use `uv` for lightning-fast deterministic package management.
   ```powershell
   uv venv --python 3.12 .venv
   .venv\Scripts\activate
   uv pip install -e ".[dev]"
   ```

2. **Configuration**:
   Copy `.env.example` to `.env` and fill out relevant keys.

---

## Adding a New Tool

1. Create a tool class inheriting from `BaseTool` in the appropriate `tools/<domain>/` subfolder.
2. Define a Pydantic `args_schema` for strongly typed validation.
3. Assign an appropriate `RiskLevel` (`SAFE`, `SENSITIVE`, or `CRITICAL`).
4. Implement `async def run(...)` and concrete environmental assertions in `async def verify(...)`.
5. Register the tool in `core/orchestrator/orchestrator.py` or dynamically via `registry.register(MyTool())`.
6. Add unit tests under `tests/test_tools.py`.

---

## Coding Standards
- Modern Python 3.12+ syntax (type annotations, union operators `|`, pattern matching).
- All I/O operations must be asynchronous or offloaded to thread executors via `loop.run_in_executor()`.
- Zero raw secrets in code or git commits.
