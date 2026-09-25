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

    # skill (universal skills & extensibility)
    skill_parser = subparsers.add_parser("skill", help="Manage universal skills and plugins")
    skill_sub = skill_parser.add_subparsers(dest="skill_action")

    skill_sub.add_parser("list", help="List installed skills")

    info_p = skill_sub.add_parser("info", help="Show skill details")
    info_p.add_argument("name", help="Skill name")

    install_p = skill_sub.add_parser("install", help="Install a skill package")
    install_p.add_argument("path", help="Directory path to skill package")
    install_p.add_argument("--yes", "-y", action="store_true", help="Confirm installation permissions")

    enable_p = skill_sub.add_parser("enable", help="Enable an installed skill")
    enable_p.add_argument("name", help="Skill name")

    disable_p = skill_sub.add_parser("disable", help="Disable an active skill")
    disable_p.add_argument("name", help="Skill name")

    update_p = skill_sub.add_parser("update", help="Update a skill package")
    update_p.add_argument("name", help="Skill name")
    update_p.add_argument("path", help="Path to new skill package")
    update_p.add_argument("--yes", "-y", action="store_true", help="Confirm permission escalation")

    uninstall_p = skill_sub.add_parser("uninstall", help="Uninstall a skill")
    uninstall_p.add_argument("name", help="Skill name")
    uninstall_p.add_argument("--purge-data", action="store_true", help="Delete isolated user data")

    scaffold_p = skill_sub.add_parser("scaffold", help="Scaffold a new skill package")
    scaffold_p.add_argument("name", help="Skill name")
    scaffold_p.add_argument("--type", default="api", choices=["api", "tool", "app"], help="Template type")
    scaffold_p.add_argument("--out", default=".", help="Output directory")

    # Automation subcommands
    auto_parser = subparsers.add_parser("automation", help="Manage proactive automations, routines, and schedules")
    auto_sub = auto_parser.add_subparsers(dest="automation_action")

    auto_list_p = auto_sub.add_parser("list", help="List registered automations")
    auto_list_p.add_argument("--status", choices=["active", "paused", "disabled"], help="Filter by status")

    auto_create_p = auto_sub.add_parser("create", help="Create automation from natural language prompt")
    auto_create_p.add_argument("prompt", help="Natural language prompt")

    auto_edit_p = auto_sub.add_parser("edit", help="Edit automation using natural language")
    auto_edit_p.add_argument("id", help="Automation ID")
    auto_edit_p.add_argument("prompt", help="Modification prompt")

    auto_enable_p = auto_sub.add_parser("enable", help="Enable automation")
    auto_enable_p.add_argument("id", help="Automation ID")

    auto_disable_p = auto_sub.add_parser("disable", help="Disable automation")
    auto_disable_p.add_argument("id", help="Automation ID")

    auto_pause_p = auto_sub.add_parser("pause", help="Pause automation")
    auto_pause_p.add_argument("id", help="Automation ID")

    auto_resume_p = auto_sub.add_parser("resume", help="Resume automation")
    auto_resume_p.add_argument("id", help="Automation ID")

    auto_run_p = auto_sub.add_parser("run", help="Run automation immediately")
    auto_run_p.add_argument("id", help="Automation ID")
    auto_run_p.add_argument("--dry-run", action="store_true", help="Simulate execution without side-effects")

    auto_hist_p = auto_sub.add_parser("history", help="View automation execution history")
    auto_hist_p.add_argument("id", nargs="?", default=None, help="Optional automation ID")
    auto_hist_p.add_argument("--limit", type=int, default=20, help="Max run entries to display")

    auto_val_p = auto_sub.add_parser("validate", help="Validate automation file")
    auto_val_p.add_argument("path", help="Path to automation JSON file")

    auto_doc_p = auto_sub.add_parser("doctor", help="Inspect automation subsystem health and metrics")

    # Phase 16: project
    project_parser = subparsers.add_parser("project", help="Manage projects and project context")
    project_sub = project_parser.add_subparsers(dest="project_action")
    proj_list_p = project_sub.add_parser("list", help="List all projects")
    proj_list_p.add_argument("--status", default=None, help="Filter by status")
    proj_create_p = project_sub.add_parser("create", help="Create a project")
    proj_create_p.add_argument("name", help="Project name")
    proj_create_p.add_argument("--description", "-d", default="", help="Description")
    proj_create_p.add_argument("--path", default=None, help="Local codebase path")
    proj_ctx_p = project_sub.add_parser("context", help="View project context snapshot")
    proj_ctx_p.add_argument("name_or_id", help="Project name or ID")
    proj_stat_p = project_sub.add_parser("status", help="View project health and status")
    proj_stat_p.add_argument("name_or_id", help="Project name or ID")

    # Phase 16: goal
    goal_parser = subparsers.add_parser("goal", help="Manage strategic personal goals")
    goal_sub = goal_parser.add_subparsers(dest="goal_action")
    goal_sub.add_parser("list", help="List all goals")
    goal_create_p = goal_sub.add_parser("create", help="Create a goal")
    goal_create_p.add_argument("title", help="Goal title")
    goal_create_p.add_argument("--category", "-c", default="General", help="Category")
    goal_create_p.add_argument("--due", default=None, help="Target completion date")
    goal_prog_p = goal_sub.add_parser("progress", help="View goal progress")
    goal_prog_p.add_argument("id", help="Goal ID")

    # Phase 16: plan
    plan_parser = subparsers.add_parser("plan", help="Daily and weekly planning")
    plan_sub = plan_parser.add_subparsers(dest="plan_action")
    plan_today_p = plan_sub.add_parser("today", help="Generate proposed day plan")
    plan_today_p.add_argument("--hours", type=float, default=8.0, help="Available hours today")

    # Phase 16: review
    review_parser = subparsers.add_parser("review", help="Productivity reviews and retrospectives")
    review_sub = review_parser.add_subparsers(dest="review_action")
    review_sub.add_parser("week", help="View weekly review")

    # Phase 17: computer
    comp_parser = subparsers.add_parser("computer", help="Computer autonomy and desktop operations")
    comp_sub = comp_parser.add_subparsers(dest="computer_action")
    comp_sub.add_parser("status", help="View computer autonomy status")
    comp_sub.add_parser("observe", help="Capture and display desktop observation")
    comp_sub.add_parser("windows", help="List visible desktop windows")
    comp_sub.add_parser("monitors", help="List display monitors")
    comp_sub.add_parser("doctor", help="Run computer autonomy diagnostics")
    comp_sub.add_parser("test", help="Execute synthetic closed-loop GUI test")
    comp_sub.add_parser("stop", help="Trigger emergency stop")

    # Phase 18: device
    dev_parser = subparsers.add_parser("device", help="Cross-device mesh and ambient operations")
    dev_sub = dev_parser.add_subparsers(dest="device_action")
    dev_list_p = dev_sub.add_parser("list", help="List all mesh devices")
    dev_list_p.add_argument("--state", help="Filter by trust state (e.g. trusted, discovered)")
    dev_pair_p = dev_sub.add_parser("pair", help="Initiate or confirm pairing")
    dev_pair_p.add_argument("--name", default="Shivani Companion", help="Device display name")
    dev_pair_p.add_argument("--platform", default="android", help="Platform: android, windows, tablet")
    dev_pair_p.add_argument("--confirm", action="store_true", help="Confirm pairing code")
    dev_pair_p.add_argument("--session-id", dest="session_id", help="Pairing session ID")
    dev_pair_p.add_argument("--code", help="6-digit pairing code")
    dev_rev_p = dev_sub.add_parser("revoke", help="Revoke device trust")
    dev_rev_p.add_argument("device_id", help="Target device ID to revoke")
    dev_hdf_p = dev_sub.add_parser("handoff", help="Initiate task handoff")
    dev_hdf_p.add_argument("task_id", help="Task ID")
    dev_hdf_p.add_argument("--target", required=True, help="Target device ID")
    dev_tx_p = dev_sub.add_parser("transfer", help="Transfer file across devices")
    dev_tx_p.add_argument("file", help="Local file path")
    dev_tx_p.add_argument("--target", required=True, help="Target device ID")
    dev_sub.add_parser("stop", help="Global emergency stop all devices")

    # Phase 19: ai
    ai_parser = subparsers.add_parser("ai", help="Local AI, model routing, benchmarking & offline autonomy")
    ai_sub = ai_parser.add_subparsers(dest="ai_action")
    ai_sub.add_parser("status", help="View AI subsystem status and metrics")

    ai_models_p = ai_sub.add_parser("models", help="List cataloged models")
    ai_models_p.add_argument("--provider", help="Filter by provider: local, cloud, specialized, deterministic")
    ai_models_p.add_argument("--capability", help="Filter by capability")

    ai_route_p = ai_sub.add_parser("route", help="Evaluate model routing for a prompt")
    ai_route_p.add_argument("query", help="Prompt or task query to route")
    ai_route_p.add_argument("--privacy", choices=["public", "low_sensitivity", "private", "sensitive", "critical"], help="Privacy tier")
    ai_route_p.add_argument("--local", action="store_true", help="Force local model preference")
    ai_route_p.add_argument("--strategy", help="Routing strategy: auto, local_first, cloud_first, speed_first, cost_aware, privacy_first")

    ai_bench_p = ai_sub.add_parser("benchmark", help="Run benchmark on model")
    ai_bench_p.add_argument("--model", default="llama3.1:8b", help="Model ID to benchmark")

    ai_sub.add_parser("doctor", help="Run AI Doctor diagnostics")

    ai_off_p = ai_sub.add_parser("offline", help="Inspect or toggle offline mode")
    ai_off_p.add_argument("--force", action="store_true", help="Force offline mode")
    ai_off_p.add_argument("--online", action="store_true", help="Restore online mode")

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
        if args.query.lower() in ("list", "create", "complete", "defer", "search") or any(args.query.startswith(p) for p in ("list ", "create ", "complete ", "defer ", "search ")):
            from cli.productivity_cli import handle_task_cli
            parts = args.query.split(" ", 1)
            args.task_action = parts[0].lower()
            if len(parts) > 1:
                if args.task_action == "create":
                    args.title = parts[1]
                elif args.task_action in ("complete", "defer"):
                    args.id = parts[1]
                elif args.task_action == "search":
                    args.query = parts[1]
            return handle_task_cli(args)
        return asyncio.run(run_task_cmd(args.query, safe_mode=args.safe_mode, demo_mode=args.demo))
    elif args.command == "project":
        from cli.productivity_cli import handle_project_cli
        return handle_project_cli(args)
    elif args.command == "goal":
        from cli.productivity_cli import handle_goal_cli
        return handle_goal_cli(args)
    elif args.command == "plan":
        from cli.productivity_cli import handle_plan_cli
        return handle_plan_cli(args)
    elif args.command == "review":
        from cli.productivity_cli import handle_review_cli
        return handle_review_cli(args)
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
    elif args.command == "skill":
        from cli.skill_cli import handle_skill_cli
        return handle_skill_cli(args)
    elif args.command == "automation":
        from cli.automation_cli import handle_automation_cli
        return handle_automation_cli(args)
    elif args.command == "computer":
        from cli.computer_cli import (
            run_computer_status,
            run_computer_observe,
            run_computer_windows,
            run_computer_monitors,
            run_computer_doctor,
            run_computer_test,
            run_computer_stop,
        )
        action = getattr(args, "computer_action", "status") or "status"
        if action == "status":
            run_computer_status()
        elif action == "observe":
            run_computer_observe()
        elif action == "windows":
            run_computer_windows()
        elif action == "monitors":
            run_computer_monitors()
        elif action == "doctor":
            run_computer_doctor()
        elif action == "test":
            run_computer_test()
        elif action == "stop":
            run_computer_stop()
        return 0
    elif args.command == "device":
        from cli.device_cli import handle_device_cli
        return handle_device_cli(args)
    elif args.command == "ai":
        from cli.ai_cli import handle_ai_cli
        return handle_ai_cli(args)
    else:

        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
