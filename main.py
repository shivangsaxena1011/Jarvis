"""
SHIVANI - Personal Autonomous AI Computer Agent
Main entrypoint supporting Server (FastAPI + Web Dashboard), CLI, and One-Shot tasks.
"""

import sys
import argparse
import asyncio
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.config import get_settings
from core.orchestrator.orchestrator import Orchestrator
from core.orchestrator.state_machine import TaskState

console = Console()


def print_banner(settings):
    banner = f"""[bold cyan]SHIVANI[/bold cyan] — Personal Autonomous AI Computer Agent
[dim]Version 0.1.0 | Platform: Windows | Principle: OBSERVE -> PLAN -> ACT -> VERIFY[/dim]
Provider: [bold green]{settings.LLM_PROVIDER.upper()}[/bold green] ({settings.LLM_MODEL})
Security Policy: [bold yellow]{settings.SECURITY_POLICY.upper()}[/bold yellow]
Dashboard URL: [link=http://{settings.HOST}:{settings.PORT}]http://{settings.HOST}:{settings.PORT}[/link]
"""
    console.print(Panel(banner, border_style="cyan"))


async def run_one_shot(query: str):
    settings = get_settings()
    print_banner(settings)
    orchestrator = Orchestrator(settings=settings)

    console.print(f"[bold yellow]Submitting Task:[/bold yellow] {query}")
    task = await orchestrator.submit_task(query)

    # Wait for completion
    while task.state in (TaskState.PENDING, TaskState.PLANNING, TaskState.WAITING_FOR_PERMISSION, TaskState.EXECUTING, TaskState.VERIFYING):
        # Auto-approve for non-interactive test if requested or pending
        pending = orchestrator.permissions.list_pending_requests()
        for p in pending:
            console.print(f"[bold magenta]Auto-approving permission request:[/bold magenta] {p.tool_name} ({p.risk_level.value})")
            orchestrator.approve_request(p.id, True, resolved_by="cli_auto")
        await asyncio.sleep(0.5)

    console.print(f"\n[bold green]Final Task State:[/bold green] {task.state.value}")
    if task.plan:
        table = Table(title="Execution Steps & Verification")
        table.add_column("Step", style="cyan")
        table.add_column("Tool", style="magenta")
        table.add_column("Action", style="white")
        table.add_column("Status", style="green")
        table.add_column("Verification", style="dim")

        for idx, res in enumerate(task.step_results):
            status = "[green]SUCCESS[/green]" if res.success else f"[red]FAILED: {res.error}[/red]"
            verified = "[green]VERIFIED[/green]" if res.verification.get("verified") else "[red]UNVERIFIED[/red]"
            table.add_row(f"{idx+1}", res.tool, res.action, status, verified)

        console.print(table)

    if task.error:
        console.print(f"[bold red]Error:[/bold red] {task.error}")
    else:
        console.print(f"[bold cyan]Result:[/bold cyan] {task.final_output}")

    await orchestrator.shutdown()


def main():
    # If first argument is a CLI subcommand, delegate to cli.main
    cli_commands = {"doctor", "status", "config", "logs", "task", "start", "stop"}
    if len(sys.argv) > 1 and sys.argv[1] in cli_commands:
        from cli.main import main as cli_entry
        sys.exit(cli_entry())

    parser = argparse.ArgumentParser(description="SHIVANI Autonomous Personal AI Agent")
    parser.add_argument("--host", default=None, help="Host address to bind")
    parser.add_argument("--port", type=int, default=None, help="Port to listen on")
    parser.add_argument("--task", type=str, default=None, help="Execute a single task and exit")
    parser.add_argument("--dry-run", action="store_true", help="Validate setup, configuration, tools, and exit")
    parser.add_argument("--open-browser", action="store_true", help="Automatically open browser dashboard upon startup")
    args = parser.parse_args()

    settings = get_settings()

    if args.dry_run:
        print_banner(settings)
        orch = Orchestrator(settings=settings)
        tools = orch.tools.list_tools()
        console.print(f"[bold green]Setup Verified Successfully![/bold green] Registered Tools: {len(tools)}")
        sys.exit(0)

    if args.task:
        asyncio.run(run_one_shot(args.task))
        sys.exit(0)

    # Server mode
    host = args.host or settings.HOST
    port = args.port or settings.PORT
    print_banner(settings)
    console.print(f"[bold green]Starting SHIVANI Desktop Server on http://{host}:{port}[/bold green]")
    
    if args.open_browser:
        import threading
        import time
        import webbrowser

        def _launch_browser():
            time.sleep(1.2)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=_launch_browser, daemon=True).start()

    uvicorn.run("apps.desktop.server:app", host=host, port=port, reload=False, log_level="info")


if __name__ == "__main__":
    main()

