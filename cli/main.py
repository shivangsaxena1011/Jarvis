"""
SHIVANI Unified Command Line Interface (CLI)
Provides operators and end-users with full control over the runtime, diagnostics,
tasks, recovery, security, logs, and configuration.
"""

import sys
import os
import argparse
import asyncio
import json
from typing import Optional

from core.config import get_settings
from core.config.app_dirs import get_app_dirs
from observability.diagnostics import DIAGNOSTICS
from observability.health import HEALTH
from observability.performance import PROFILER


def run_doctor_cmd(full: bool = False) -> int:
    """Executes environment and system doctor checks."""
    if full:
        items = DIAGNOSTICS.run_full_doctor()
    else:
        items = DIAGNOSTICS.run_quick_doctor()

    output = DIAGNOSTICS.format_cli_output(items, full=full)
    print(output)
    has_failure = any(not item.passed and item.severity == "FAIL" for item in items)
    return 1 if has_failure else 0


def run_status_cmd() -> int:
    """Displays current system status, health, and resource metrics."""
    health_data = HEALTH.check_overall_health()
    perf = PROFILER.get_summary()

    print("=== SHIVANI SYSTEM STATUS ===")
    print(f"Overall Health: {health_data['overall_status']}")
    print(f"PID: {perf['pid']} | CPU: {perf['cpu_percent']}% | Memory: {perf['memory_mb']} MB ({perf['memory_percent']}%)")
    print("\nSubsystem Statuses:")
    for name, comp in health_data.get("components", {}).items():
        print(f"  [{comp['status']}] {name:<12}: {comp['message']}")

    dirs = get_app_dirs()
    print(f"\nAppData Location: {dirs.root_dir}")
    return 0


def run_config_cmd() -> int:
    """Displays active configuration and data paths."""
    settings = get_settings()
    dirs = get_app_dirs()

    print("=== SHIVANI CONFIGURATION ===")
    print(f"Environment    : {settings.ENV}")
    print(f"LLM Provider   : {settings.LLM_PROVIDER} ({settings.LLM_MODEL})")
    print(f"Security Policy: {settings.SECURITY_POLICY}")
    print(f"Voice Enabled  : {settings.VOICE_ENABLED}")
    print("\nDirectories:")
    print(f"  Root Dir     : {dirs.root_dir}")
    print(f"  Config Dir   : {dirs.config_dir}")
    print(f"  Data/Vault   : {dirs.data_dir}")
    print(f"  Logs Dir     : {dirs.logs_dir}")
    print(f"  Memory Dir   : {dirs.memory_dir}")
    print(f"  Backups Dir  : {dirs.backups_dir}")
    return 0


def run_logs_cmd(lines: int = 50) -> int:
    """Displays recent audit log entries."""
    from security.audit_logger import AUDIT_LOGGER
    events = AUDIT_LOGGER.get_recent_events(limit=lines)
    print(f"=== SHIVANI AUDIT LOG (Last {len(events)} events) ===")
    if not events:
        print("No recent audit log entries found.")
        return 0

    for ev in events:
        ts = ev.get("timestamp", "")
        sev = ev.get("severity", "INFO")
        action = ev.get("action", "unknown")
        details = json.dumps(ev.get("details", {}))
        print(f"[{ts}] [{sev}] {action} -> {details}")
    return 0


async def run_task_cmd(query: str, safe_mode: bool = False, demo_mode: bool = False) -> int:
    """Executes a single user instruction from the command line."""
    from core.orchestrator.orchestrator import Orchestrator
    from core.orchestrator.state_machine import TaskState

    if safe_mode:
        os.environ["SHIVANI_SAFE_MODE"] = "1"
    if demo_mode:
        os.environ["SHIVANI_DEMO_MODE"] = "1"

    settings = get_settings()
    orchestrator = Orchestrator(settings=settings)

    print(f"Submitting Task: '{query}'")
    if safe_mode:
        print("[SAFE MODE ENABLED - Prohibiting dangerous commands and external mutations]")
    if demo_mode:
        print("[DEMO MODE ENABLED - Simulating all actions safely]")

    task = await orchestrator.submit_task(query)

    while task.state in (TaskState.PENDING, TaskState.PLANNING, TaskState.WAITING_FOR_PERMISSION, TaskState.EXECUTING, TaskState.VERIFYING):
        pending = orchestrator.permissions.list_pending_requests()
        for p in pending:
            print(f"Auto-approving permission request: {p.tool_name} ({p.risk_level.value})")
            orchestrator.approve_request(p.id, True, resolved_by="cli")
        await asyncio.sleep(0.5)

    print(f"\nFinal State: {task.state.value}")
    if task.error:
        print(f"Error: {task.error}")
        await orchestrator.shutdown()
        return 1

    print(f"Result: {task.final_output}")
    await orchestrator.shutdown()
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="shivani", description="SHIVANI Personal Autonomous AI Computer Agent")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # doctor
    doctor_parser = subparsers.add_parser("doctor", help="Run system diagnostics and dependency checks")
    doctor_parser.add_argument("--full", action="store_true", help="Run full diagnostic suite including Ollama & disk")

    # status
    subparsers.add_parser("status", help="Show system health and resource consumption")

    # config
    subparsers.add_parser("config", help="Inspect configuration settings and AppData directories")

    # logs
    logs_parser = subparsers.add_parser("logs", help="View recent audit logs")
    logs_parser.add_argument("-n", "--lines", type=int, default=50, help="Number of log lines to show")

    # task
    task_parser = subparsers.add_parser("task", help="Execute an autonomous task")
    task_parser.add_argument("query", type=str, help="Instruction for SHIVANI")
    task_parser.add_argument("--safe-mode", action="store_true", help="Run in restricted Safe Mode")
    task_parser.add_argument("--demo", action="store_true", help="Run in Demo Mode with simulated side-effects")

    # start (server)
    start_parser = subparsers.add_parser("start", help="Start SHIVANI Desktop Server")
    start_parser.add_argument("--host", default=None)
    start_parser.add_argument("--port", type=int, default=None)

    # stop (emergency stop)
    subparsers.add_parser("stop", help="Trigger Emergency Stop across all active tasks")

    args = parser.parse_args(argv)

    if args.command == "doctor":
        return run_doctor_cmd(full=args.full)
    elif args.command == "status":
        return run_status_cmd()
    elif args.command == "config":
        return run_config_cmd()
    elif args.command == "logs":
        return run_logs_cmd(lines=args.lines)
    elif args.command == "task":
        return asyncio.run(run_task_cmd(args.query, safe_mode=args.safe_mode, demo_mode=args.demo))
    elif args.command == "start":
        settings = get_settings()
        import uvicorn
        host = args.host or settings.HOST
        port = args.port or settings.PORT
        uvicorn.run("apps.desktop.server:app", host=host, port=port, reload=False, log_level="info")
        return 0
    elif args.command == "stop":
        from core.orchestrator.emergency import EmergencyStop
        es = EmergencyStop()
        stopped = es.trigger_stop_all()
        print(f"Emergency Stop triggered. Aborted {stopped} active tasks and triggered all shutdown hooks.")
        return 0
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
