"""
SHIVANI Automation CLI Subcommand Handler (Phase 15).
CLI interface for managing proactive automations, routines, schedules, and history:
  shivani automation list
  shivani automation create "<prompt>"
  shivani automation edit <id> "<prompt>"
  shivani automation enable <id>
  shivani automation disable <id>
  shivani automation run <id>
  shivani automation pause <id>
  shivani automation resume <id>
  shivani automation history [id]
  shivani automation validate <file_path>
  shivani automation doctor
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

from core.automation.dsl import AutomationDSL
from core.automation.engine import AutomationEngine
from core.automation.models import AutomationStatus


def handle_automation_cli(args) -> int:
    action = getattr(args, "automation_action", None)
    if not action:
        print("Usage: shivani automation {list|create|edit|enable|disable|run|pause|resume|history|validate|doctor} [options]")
        return 1

    engine = AutomationEngine()

    if action == "list":
        return _handle_list(engine, getattr(args, "status", None))
    elif action == "create":
        return _handle_create(engine, args.prompt)
    elif action == "edit":
        return _handle_edit(engine, args.id, args.prompt)
    elif action == "enable":
        return _handle_enable(engine, args.id)
    elif action == "disable":
        return _handle_disable(engine, args.id)
    elif action == "run":
        return asyncio.run(_handle_run(engine, args.id, getattr(args, "dry_run", False)))
    elif action == "pause":
        return _handle_pause(engine, args.id)
    elif action == "resume":
        return _handle_resume(engine, args.id)
    elif action == "history":
        return _handle_history(engine, getattr(args, "id", None), getattr(args, "limit", 20))
    elif action == "validate":
        return _handle_validate(args.path)
    elif action == "doctor":
        return _handle_doctor(engine)
    else:
        print(f"Unknown automation action: {action}")
        return 1


def _handle_list(engine: AutomationEngine, status_filter: Optional[str] = None) -> int:
    stat = None
    if status_filter:
        try:
            stat = AutomationStatus(status_filter.upper())
        except ValueError:
            pass

    automations = engine.list_automations(status=stat)
    print("=== SHIVANI REGISTERED AUTOMATIONS ===")
    if not automations:
        print("  No automations registered. Use 'shivani automation create \"<prompt>\"' to add one.")
        return 0

    for a in automations:
        stat_bullet = "[*]" if a.enabled and a.status == AutomationStatus.ACTIVE else "[ ]"
        print(f"\n  {stat_bullet} {a.name} (ID: {a.id})")
        print(f"    Status   : {a.status.value} (v{a.version})")
        print(f"    Trigger  : {a.trigger.type.value}")
        if a.next_run:
            print(f"    Next Run : {a.next_run}")
        if a.last_run:
            print(f"    Last Run : {a.last_run}")
        print(f"    Steps ({len(a.steps)}): {', '.join(s.name or s.action for s in a.steps[:3])}")
    return 0


def _handle_create(engine: AutomationEngine, prompt: str) -> int:
    print(f"Compiling automation from prompt: '{prompt}'...")
    auto = engine.create_from_prompt(prompt)
    preview = engine.preview_automation(auto)

    print("\n=== AUTOMATION CREATED ===")
    print(f"ID         : {auto.id}")
    print(f"Name       : {auto.name}")
    print(f"Runs       : {preview['runs']}")
    print(f"Actions    : {', '.join(preview['actions'])}")
    print(f"Max Risk   : {preview['max_risk_level']}")
    print(f"Conditions : {preview['conditions_summary']}")
    print("\nAutomation saved and activated in local store.")
    return 0


def _handle_edit(engine: AutomationEngine, auto_id: str, prompt: str) -> int:
    updated = engine.edit_from_prompt(auto_id, prompt)
    if not updated:
        print(f"Error: Automation '{auto_id}' not found.")
        return 1
    print(f"Automation '{updated.name}' updated to version {updated.version}.")
    return 0


def _handle_enable(engine: AutomationEngine, auto_id: str) -> int:
    if engine.enable_automation(auto_id):
        print(f"Automation '{auto_id}' ENABLED.")
        return 0
    print(f"Error: Automation '{auto_id}' not found.")
    return 1


def _handle_disable(engine: AutomationEngine, auto_id: str) -> int:
    if engine.disable_automation(auto_id):
        print(f"Automation '{auto_id}' DISABLED.")
        return 0
    print(f"Error: Automation '{auto_id}' not found.")
    return 1


def _handle_pause(engine: AutomationEngine, auto_id: str) -> int:
    if engine.pause_automation(auto_id):
        print(f"Automation '{auto_id}' PAUSED.")
        return 0
    print(f"Error: Automation '{auto_id}' not found.")
    return 1


def _handle_resume(engine: AutomationEngine, auto_id: str) -> int:
    if engine.resume_automation(auto_id):
        print(f"Automation '{auto_id}' RESUMED.")
        return 0
    print(f"Error: Automation '{auto_id}' not found.")
    return 1


async def _handle_run(engine: AutomationEngine, auto_id: str, dry_run: bool = False) -> int:
    print(f"Triggering automation '{auto_id}' (dry_run={dry_run})...")
    run = await engine.run_automation_now(auto_id, dry_run=dry_run)
    if not run:
        print(f"Error: Automation '{auto_id}' not found.")
        return 1

    print("\n=== EXECUTION RUN RESULT ===")
    print(f"Run ID     : {run.id}")
    print(f"Status     : {run.status.value}")
    print(f"Started    : {run.started_at}")
    print(f"Completed  : {run.completed_at}")
    print("\nSteps Executed:")
    for s in run.steps:
        print(f"  * {s.name or s.tool} -> {s.status} ({s.duration_ms}ms)")
        if s.error:
            print(f"    Error: {s.error}")
    return 0 if run.status.value == "COMPLETED" else 1


def _handle_history(engine: AutomationEngine, auto_id: Optional[str] = None, limit: int = 20) -> int:
    runs = engine.get_history(automation_id=auto_id, limit=limit)
    print("=== AUTOMATION RUN HISTORY ===")
    if not runs:
        print("  No execution runs found.")
        return 0

    for r in runs:
        print(f"  [{r.status.value}] {r.automation_name} | Run: {r.id[:8]} | Time: {r.started_at}")
        if r.errors:
            print(f"    Errors: {'; '.join(r.errors)}")
    return 0


def _handle_validate(file_path: str) -> int:
    p = Path(file_path)
    if not p.exists():
        print(f"Error: File '{file_path}' does not exist.")
        return 1

    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        ok, errs, auto = AutomationDSL.validate_automation(data)
        if ok and auto:
            print(f"Validation SUCCESS: Automation '{auto.name}' is valid.")
            preview = AutomationDSL.generate_preview(auto)
            print(json.dumps(preview, indent=2))
            return 0
        else:
            print("Validation FAILED with errors:")
            for e in errs:
                print(f"  * {e}")
            return 1
    except Exception as e:
        print(f"Validation error: {e}")
        return 1


def _handle_doctor(engine: AutomationEngine) -> int:
    analytics = engine.get_analytics()
    print("=== AUTOMATION SYSTEM DOCTOR ===")
    print(f"Total Automations : {analytics['total_automations']}")
    print(f"Active            : {analytics['active']}")
    print(f"Paused            : {analytics['paused']}")
    print(f"Needs Attention   : {analytics['needs_attention']}")
    print(f"Total Runs        : {analytics['total_runs']}")
    print(f"Success Rate      : {analytics['success_rate']}%")
    print(f"Successful Runs   : {analytics['successful_runs']}")
    print(f"Failed Runs       : {analytics['failed_runs']}")

    if analytics['needs_attention'] > 0:
        print("\n[WARNING] Some automations have repeated failures. Review with 'shivani automation history'.")
    else:
        print("\n[OK] Automation subsystem is healthy and operational.")
    return 0
