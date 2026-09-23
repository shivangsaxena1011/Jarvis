# Tool System & Contracts — SHIVANI

Every capability in SHIVANI is implemented as a self-contained, schema-validated tool inheriting from `BaseTool`.

---

## Tool Interface Contract

```python
class BaseTool(ABC):
    name: str                       # Canonical tool identifier (e.g. 'computer.screenshot')
    description: str                # Human and LLM readable summary
    permission_level: RiskLevel     # SAFE | SENSITIVE | CRITICAL
    timeout: float                  # Execution timeout in seconds
    retry_policy: int               # Number of retry attempts on transient failure
    args_schema: Type[BaseModel]    # Pydantic input argument schema

    async def run(self, **kwargs) -> Any:
        """Executes the specific tool operation."""
        ...

    async def verify(self, result_data: Any, **kwargs) -> Dict[str, Any]:
        """Validates physical/virtual side effects."""
        ...
```

---

## Tool Registry

| Tool Name | Domain | Risk Tier | Input Schema | Verification Strategy |
|---|---|---|---|---|
| `computer.screenshot` | Computer | `SAFE` | `filename: Optional[str]` | Validates image exists on disk and `size_bytes > 0` |
| `computer.get_active_window` | Computer | `SAFE` | None | Validates window title string presence |
| `computer.list_processes` | Computer | `SAFE` | `filter_name: Optional[str]`, `limit: int` | Validates process list count |
| `computer.open_app` | Computer | `SAFE` | `app_name: str`, `arguments: List[str]` | Checks OS process table for matching process name |
| `filesystem.list_dir` | Filesystem | `SAFE` | `path: str = "."` | Confirms path exists and returns directory entries |
| `filesystem.read_file` | Filesystem | `SAFE` | `path: str`, `max_bytes: int` | Confirms path is a file and content was read |
| `filesystem.write_file` | Filesystem | `SENSITIVE` | `path: str`, `content: str`, `append: bool` | Validates target file exists and `size_bytes >= written` |
| `filesystem.safe_delete` | Filesystem | `CRITICAL` | `path: str` | Confirms target path no longer exists on disk |
| `terminal.execute` | Terminal | `SENSITIVE` / `CRITICAL` | `command: str`, `cwd: str`, `timeout_seconds: float` | Inspects process `exit_code == 0` |

---

## Tool Execution Lifecycle

1. **Validation**: Arguments validated against tool's Pydantic schema.
2. **Permission Evaluation**: Engine verifies whether tool risk tier or parameters require explicit user confirmation.
3. **Execution**: Ran within an `asyncio.wait_for` timeout envelope.
4. **Verification**: Post-execution assertion runs `tool.verify()`.
5. **Auditing**: Sanitized parameters, timing, and verification recorded in `audit.jsonl`.
