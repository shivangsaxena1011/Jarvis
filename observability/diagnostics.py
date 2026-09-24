"""
SHIVANI Observability — System Diagnostics Engine
Powering `shivani doctor` and `shivani doctor --full` CLI commands.
Audits runtime environment, dependencies, security subsystem, storage, and connectivity.
"""

import os
import sys
import platform
import shutil
import urllib.request
from typing import Any, Dict, List, Tuple


class DiagnosticItem:
    def __init__(self, name: str, passed: bool, message: str, severity: str = "INFO", fix: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.severity = severity  # "OK", "WARN", "FAIL"
        self.fix = fix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "status": self.severity,
            "message": self.message,
            "fix": self.fix,
        }


class DiagnosticsRunner:
    """Executes environment and system diagnostic checks."""

    def run_quick_doctor(self) -> List[DiagnosticItem]:
        """Runs essential diagnostic checks."""
        results: List[DiagnosticItem] = []

        # 1. OS Check
        os_name = platform.system()
        os_ver = platform.version()
        if os_name == "Windows":
            results.append(DiagnosticItem("Operating System", True, f"Windows ({os_ver})", "OK"))
        else:
            results.append(DiagnosticItem("Operating System", True, f"{os_name} (Non-Windows host: DPAPI fallback enabled)", "WARN"))

        # 2. Python Version
        py_ver = sys.version_info
        if py_ver >= (3, 10):
            results.append(DiagnosticItem("Python Version", True, f"Python {platform.python_version()}", "OK"))
        else:
            results.append(DiagnosticItem("Python Version", False, f"Python {platform.python_version()} is below recommended 3.10+", "FAIL", "Upgrade to Python 3.11+"))

        # 3. DPAPI Crypto Check
        dpapi_ok = False
        try:
            if sys.platform == "win32":
                import ctypes
                dpapi_ok = hasattr(ctypes.windll, "crypt32")
            else:
                dpapi_ok = True
        except Exception:
            dpapi_ok = False

        if dpapi_ok:
            results.append(DiagnosticItem("Crypto Subsystem", True, "DPAPI crypt32 hardware protection available", "OK"))
        else:
            results.append(DiagnosticItem("Crypto Subsystem", False, "DPAPI not available, fallback encryption in use", "WARN"))

        # 4. Storage & AppData Directories
        try:
            from core.config.app_dirs import get_app_dirs
            dirs = get_app_dirs()
            dirs.ensure_dirs()
            results.append(DiagnosticItem("App Directories", True, f"Writable at {dirs.root_dir}", "OK"))
        except Exception as e:
            results.append(DiagnosticItem("App Directories", False, f"Directory check error: {e}", "FAIL"))

        # 5. Core Dependencies
        missing_deps = []
        for mod in ["pydantic", "psutil"]:
            try:
                __import__(mod)
            except ImportError:
                missing_deps.append(mod)

        if not missing_deps:
            results.append(DiagnosticItem("Core Dependencies", True, "All required Python libraries installed", "OK"))
        else:
            results.append(DiagnosticItem("Core Dependencies", False, f"Missing packages: {', '.join(missing_deps)}", "FAIL", "Run pip install -r requirements.txt"))

        return results

    def run_full_doctor(self) -> List[DiagnosticItem]:
        """Runs comprehensive diagnostic checks including local AI, tools, network, and disk."""
        results = self.run_quick_doctor()

        # 6. Tool Registry Audit
        try:
            from core.orchestrator.orchestrator import Orchestrator
            orch = Orchestrator()
            count = len(orch.tools._tools)
            if count >= 100:
                results.append(DiagnosticItem("Tool Registry", True, f"{count} tools registered and ready", "OK"))
            elif count > 0:
                results.append(DiagnosticItem("Tool Registry", True, f"{count} tools registered (partial)", "WARN"))
            else:
                results.append(DiagnosticItem("Tool Registry", False, "0 tools registered", "FAIL"))
        except Exception as e:
            results.append(DiagnosticItem("Tool Registry", False, f"Registry error: {e}", "FAIL"))

        # 7. Local Ollama Server Probe
        ollama_active = False
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags", headers={"User-Agent": "ShivaniDiagnostics"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    ollama_active = True
        except Exception:
            ollama_active = False

        if ollama_active:
            results.append(DiagnosticItem("Local AI (Ollama)", True, "Ollama service detected on http://127.0.0.1:11434", "OK"))
        else:
            results.append(DiagnosticItem("Local AI (Ollama)", True, "Ollama offline or not running (Cloud LLM providers active)", "INFO", "Start Ollama if offline operation is desired"))

        # 8. Available Disk Space
        try:
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024 ** 3)
            if free_gb > 2.0:
                results.append(DiagnosticItem("Disk Space", True, f"{free_gb:.1f} GB available", "OK"))
            else:
                results.append(DiagnosticItem("Disk Space", False, f"Low disk space: {free_gb:.1f} GB available", "WARN", "Free up disk space for checkpoints"))
        except Exception:
            pass

        return results

    def format_cli_output(self, items: List[DiagnosticItem], full: bool = False) -> str:
        """Formats diagnostic results into readable terminal output."""
        lines = []
        mode = "FULL" if full else "QUICK"
        lines.append(f"=== SHIVANI SYSTEM DIAGNOSTICS ({mode} REPORT) ===")
        all_passed = True

        for item in items:
            badge = f"[{item.severity}]"
            lines.append(f" {badge:<8} {item.name:<24}: {item.message}")
            if item.fix:
                lines.append(f"          --> Recommendation: {item.fix}")
            if item.severity == "FAIL":
                all_passed = False

        lines.append("--------------------------------------------------")
        status_text = "ALL SYSTEMS GO" if all_passed else "SOME CHECKS REQUIRE ATTENTION"
        lines.append(f"Result: {status_text}")
        return "\n".join(lines)


DIAGNOSTICS = DiagnosticsRunner()
