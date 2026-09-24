"""
SHIVANI Productivity OS CLI Handlers (Phase 16).
Provides command-line interfaces for:
  shivani task list / create / complete / defer / search
  shivani project list / create / context / status
  shivani goal list / create / progress
  shivani plan today / week
  shivani review week
"""

import sys
from typing import Any, Optional

from core.productivity.models import TaskPriority, TaskStatus
from core.productivity.orchestrator import ProductivityOrchestrator


def _get_orchestrator() -> ProductivityOrchestrator:
    return ProductivityOrchestrator()


# ==============================================================================
# TASK CLI
# ==============================================================================

def handle_task_cli(args) -> int:
    action = getattr(args, "task_action", None)
    if not action or action == "list":
        return _task_list(getattr(args, "status", None), getattr(args, "project", None))
    elif action == "create":
        return _task_create(args.title, getattr(args, "priority", "MEDIUM"), getattr(args, "due", None), getattr(args, "project", None))
    elif action == "complete":
        return _task_complete(args.id, getattr(args, "notes", ""))
    elif action == "defer":
        return _task_defer(args.id, getattr(args, "due", None))
    elif action == "search":
        return _task_search(args.query)
    else:
        print(f"Unknown task action: {action}")
        return 1


def _task_list(status: Optional[str] = None, project: Optional[str] = None) -> int:
    prod = _get_orchestrator()
    tasks = prod.store.list_tasks(project_id=project, status=status)
    if not tasks:
        print("No tasks found matching criteria.")
        return 0

    print(f"\n{'ID':<16} {'STATUS':<12} {'PRIORITY':<10} {'DUE DATE':<12} {'TITLE'}")
    print("-" * 75)
    for t in tasks:
        print(f"{t.id:<16} {t.status.value:<12} {t.priority.value:<10} {(t.due_date or '-'):<12} {t.title}")
    print(f"\nTotal tasks: {len(tasks)}\n")
    return 0


def _task_create(title: str, priority: str = "MEDIUM", due: Optional[str] = None, project: Optional[str] = None) -> int:
    prod = _get_orchestrator()
    p_id = None
    if project:
        proj = prod.projects.get_project(project) or prod.projects.get_project_by_name(project)
        if proj:
            p_id = proj.id

    task = prod.tasks.create_task(
        title=title,
        priority=getattr(TaskPriority, priority.upper(), TaskPriority.MEDIUM),
        due_date=due,
        project_id=p_id,
    )
    print(f"[*] Created task '{task.title}' (ID: {task.id}) [Status: {task.status.value}, Priority: {task.priority.value}]")
    return 0


def _task_complete(task_id: str, notes: str = "") -> int:
    prod = _get_orchestrator()
    verified, failures = prod.tasks.complete_task(
        task_id, execution_output={"manually_confirmed": True, "notes": notes}
    )
    if not verified:
        print(f"[X] Completion gate rejected: {'; '.join(failures)}")
        return 1
    print(f"[*] Task '{task_id}' verified and marked COMPLETED.")
    return 0


def _task_defer(task_id: str, new_due: Optional[str] = None) -> int:
    prod = _get_orchestrator()
    task = prod.store.get_task(task_id)
    if not task:
        print(f"[X] Task '{task_id}' not found.")
        return 1
    task.status = TaskStatus.DEFERRED
    if new_due:
        task.due_date = new_due
    prod.store.save_task(task)
    print(f"[*] Task '{task.title}' deferred to {task.due_date or 'someday'}.")
    return 0


def _task_search(query: str) -> int:
    prod = _get_orchestrator()
    tasks = prod.store.list_tasks()
    q = query.lower()
    matches = [t for t in tasks if q in t.title.lower() or q in t.description.lower()]
    print(f"\nFound {len(matches)} task(s) matching '{query}':")
    for t in matches:
        print(f"  [{t.status.value}] {t.id} - {t.title}")
    return 0


# ==============================================================================
# PROJECT CLI
# ==============================================================================

def handle_project_cli(args) -> int:
    action = getattr(args, "project_action", None)
    if not action or action == "list":
        return _project_list(getattr(args, "status", None))
    elif action == "create":
        return _project_create(args.name, getattr(args, "description", ""), getattr(args, "path", None))
    elif action == "context":
        return _project_context(args.name_or_id)
    elif action == "status":
        return _project_status(args.name_or_id)
    else:
        print(f"Unknown project action: {action}")
        return 1


def _project_list(status: Optional[str] = None) -> int:
    prod = _get_orchestrator()
    projects = prod.store.list_projects(status=status)
    if not projects:
        print("No projects found.")
        return 0

    print(f"\n{'ID':<16} {'STATUS':<12} {'PRIORITY':<10} {'NAME'}")
    print("-" * 65)
    for p in projects:
        print(f"{p.id:<16} {p.status.value:<12} {p.priority.value:<10} {p.name}")
    print(f"\nTotal projects: {len(projects)}\n")
    return 0


def _project_create(name: str, description: str = "", path: Optional[str] = None) -> int:
    prod = _get_orchestrator()
    p = prod.projects.create_project(name=name, description=description, codebase_path=path)
    print(f"[*] Created project '{p.name}' (ID: {p.id})")
    return 0


def _project_context(name_or_id: str) -> int:
    prod = _get_orchestrator()
    summary = prod.context.get_continuity_summary(name_or_id)
    if not summary.get("found"):
        print(f"[X] {summary.get('message')}")
        return 1

    print(f"\n=== PROJECT CONTEXT: {summary['project_name']} ===")
    print(summary["summary_message"])
    print(f"Active Milestone: {summary['current_milestone']}")
    if summary["unfinished_tasks"]:
        print("\nUnfinished Tasks:")
        for t in summary["unfinished_tasks"]:
            print(f"  - [{t['status']}] {t['title']} (Due: {t['due_date'] or '-'})")
    if summary["open_blockers"]:
        print("\nOpen Blockers:")
        for b in summary["open_blockers"]:
            print(f"  [!] {b['title']}: {b['description']}")
    print()
    return 0


def _project_status(name_or_id: str) -> int:
    prod = _get_orchestrator()
    proj = prod.projects.get_project(name_or_id) or prod.projects.get_project_by_name(name_or_id)
    if not proj:
        print(f"[X] Project '{name_or_id}' not found.")
        return 1
    health = prod.projects.get_project_health(proj.id)
    print(f"\n=== PROJECT STATUS: {health['project_name']} ({health['status']}) ===")
    print(f"Open Tasks: {health['open_tasks']} | Blocked: {health['blocked_tasks']} | Overdue: {health['overdue_tasks']}")
    print(f"Milestones: {health['milestone_progress']} (Active: {health['active_milestone']})")
    if health["needs_attention"]:
        print("\nNeeds Attention:")
        for na in health["needs_attention"]:
            print(f"  - {na}")
    else:
        print("\nHealth: Healthy (No blocking issues)")
    print()
    return 0


# ==============================================================================
# GOAL CLI
# ==============================================================================

def handle_goal_cli(args) -> int:
    action = getattr(args, "goal_action", None)
    if not action or action == "list":
        return _goal_list()
    elif action == "create":
        return _goal_create(args.title, getattr(args, "category", "General"), getattr(args, "due", None))
    elif action == "progress":
        return _goal_progress(args.id)
    else:
        print(f"Unknown goal action: {action}")
        return 1


def _goal_list() -> int:
    prod = _get_orchestrator()
    goals = prod.store.list_goals()
    if not goals:
        print("No goals found.")
        return 0

    print(f"\n{'ID':<16} {'STATUS':<12} {'PROGRESS':<10} {'CATEGORY':<14} {'TITLE'}")
    print("-" * 75)
    for g in goals:
        print(f"{g.id:<16} {g.status.value:<12} {int(g.progress * 100):>3}%      {g.category:<14} {g.title}")
    print(f"\nTotal goals: {len(goals)}\n")
    return 0


def _goal_create(title: str, category: str = "General", due: Optional[str] = None) -> int:
    prod = _get_orchestrator()
    g = prod.goals.create_goal(title=title, category=category, target_date=due)
    print(f"[*] Created goal '{g.title}' (ID: {g.id})")
    return 0


def _goal_progress(goal_id: str) -> int:
    prod = _get_orchestrator()
    g = prod.goals.update_goal_progress(goal_id)
    if not g:
        print(f"[X] Goal '{goal_id}' not found.")
        return 1
    print(f"Goal '{g.title}' Progress: {int(g.progress * 100)}% ({g.status.value})")
    return 0


# ==============================================================================
# PLAN & REVIEW CLI
# ==============================================================================

def handle_plan_cli(args) -> int:
    action = getattr(args, "plan_action", "today")
    if action == "today":
        hours = getattr(args, "hours", 8.0)
        prod = _get_orchestrator()
        plan, warning = prod.planning.generate_daily_plan(available_minutes=int(hours * 60))
        print(f"\n=== PROPOSED DAILY PLAN: {plan.date} ===")
        if warning:
            print(f"[!] Warning: {warning}\n")
        for b in plan.time_blocks:
            print(f"  {b.start_time} - {b.end_time} | {b.category:<12} | {b.title}")
        print(f"\nTotal Planned: {plan.total_planned_minutes}m / {int(hours * 60)}m budget (Plan ID: {plan.id})\n")
        return 0
    else:
        print(f"Unknown plan action: {action}")
        return 1


def handle_review_cli(args) -> int:
    action = getattr(args, "review_action", "week")
    prod = _get_orchestrator()
    rev = prod.reviews.generate_weekly_review()
    print(f"\n=== WEEKLY REVIEW: {rev['period']} ===")
    print(f"- Completed Tasks: {rev['completed_tasks_count']}")
    print(f"- Projects Advanced: {rev['projects_advanced_count']} ({', '.join(rev['projects_advanced']) or 'None'})")
    print(f"- Blocked Tasks: {rev['blocked_tasks_count']}")
    print(f"- Overdue Tasks: {rev['overdue_tasks_count']}")
    print(f"- Open Blockers: {rev['open_blockers_count']}")
    print(f"- Recent Decisions: {rev['recent_decisions_count']}\n")
    return 0
