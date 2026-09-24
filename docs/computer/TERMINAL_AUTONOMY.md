# Terminal Autonomy & Command Safety — Phase 17

## 1. Safety Classifier
`TerminalSafetyClassifier` categorizes shell commands into 4 strict risk tiers:

| Tier | Patterns | Policy |
|---|---|---|
| **SAFE** | `pytest`, `git status/log/diff`, `dir`, `ls`, `python --version`, `echo`, `uv run` | Executed autonomously without user prompt. |
| **SENSITIVE** | `pip install`, `npm install`, `git checkout`, `git pull`, `curl`, `mkdir` | Executed with audit logging and rate limiting. |
| **DANGEROUS** | `rm`, `rmdir`, `del`, `format`, `diskpart`, `shutdown`, `reg delete`, `net user` | **Requires explicit interactive user confirmation.** |
| **PROHIBITED** | `rm -rf /`, `del C:\Windows\System32\*`, `vssadmin delete shadows` | **Blocked unconditionally.** |

---

## 2. Output Diagnostics Parser
When a command completes or fails, `TerminalController._parse_diagnostics` analyzes stdout and stderr:
- **Pytest**: Extracts failed test identifiers and failure traces.
- **ModuleNotFoundError**: Extracts the exact missing package name.
- **SyntaxError**: Extracts the line number and file name.
This diagnostic payload is passed directly to the calling agent to guide autonomous fixes.
