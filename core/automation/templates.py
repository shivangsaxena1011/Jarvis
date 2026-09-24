"""
SHIVANI Automation Templates (Phase 15).
Curated, safe, transparent pre-built templates for common routines and workflows.
"""

from typing import List

from core.automation.models import (
    Automation,
    AutomationNotificationPolicy,
    AutomationPermissions,
    AutomationScope,
    AutomationSource,
    AutomationStatus,
    AutomationStep,
    FailurePolicy,
    TimeSchedule,
    TriggerConfig,
    TriggerType,
)
from security.permissions.models import RiskLevel


def get_default_templates() -> List[Automation]:
    """Returns the library of standard, safe automation templates."""
    return [
        # 1. Morning Brief
        Automation(
            id="tpl_morning_brief",
            name="Morning Brief",
            description="Summarize unread important emails and pending tasks every weekday morning.",
            version=1,
            enabled=True,
            status=AutomationStatus.ACTIVE,
            scope=AutomationScope.GLOBAL,
            source=AutomationSource.TEMPLATE,
            trigger=TriggerConfig(
                type=TriggerType.SCHEDULE,
                schedule=TimeSchedule(
                    time_of_day="08:00",
                    days_of_week=["mon", "tue", "wed", "thu", "fri"],
                    timezone="Asia/Kolkata",
                ),
            ),
            steps=[
                AutomationStep(
                    step_id="step_email",
                    name="Scan Important Emails",
                    action="email.read_important",
                    tool="gmail.read_inbox",
                    input_template={"max_results": 10, "query": "is:unread is:important"},
                    expected_outcome="Unread emails fetched",
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="step_tasks",
                    name="Scan Pending Tasks",
                    action="tasks.read_pending",
                    tool="tasks.list_pending",
                    input_template={"status": "PENDING"},
                    expected_outcome="Pending tasks listed",
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="step_summary",
                    name="Generate Briefing Summary",
                    action="summary.generate",
                    tool="content.synthesize",
                    input_template={"title": "Morning Brief"},
                    expected_outcome="Briefing ready",
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="step_notify",
                    name="Deliver Morning Notification",
                    action="notify_user",
                    tool="notifications.send",
                    input_template={"title": "Morning Brief", "message": "Your morning briefing is ready."},
                    expected_outcome="User notified",
                    risk_level=RiskLevel.SAFE,
                ),
            ],
            permissions=AutomationPermissions(
                allowed_capabilities=["email", "tasks", "notifications", "knowledge"],
                max_risk_level=RiskLevel.LOW_RISK,
            ),
        ),

        # 2. Weekly Project Summary
        Automation(
            id="tpl_weekly_project_summary",
            name="Weekly Project Summary",
            description="Synthesizes weekly active git commits, tasks, and project notes every Sunday evening.",
            version=1,
            enabled=True,
            status=AutomationStatus.ACTIVE,
            scope=AutomationScope.GLOBAL,
            source=AutomationSource.TEMPLATE,
            trigger=TriggerConfig(
                type=TriggerType.SCHEDULE,
                schedule=TimeSchedule(
                    time_of_day="19:00",
                    days_of_week=["sun"],
                    timezone="Asia/Kolkata",
                ),
            ),
            steps=[
                AutomationStep(
                    step_id="s1",
                    name="Inspect Active Projects",
                    action="project.inspect_active",
                    tool="knowledge.projects",
                    input_template={},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s2",
                    name="Synthesize Weekly Progress Report",
                    action="project.synthesize_weekly",
                    tool="content.synthesize",
                    input_template={"timeframe": "7d"},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s3",
                    name="Save Project Digest Artifact",
                    action="artifact.save",
                    tool="artifacts.save",
                    input_template={"category": "digests", "title": "weekly_project_review.md"},
                    risk_level=RiskLevel.LOW_RISK,
                ),
            ],
            permissions=AutomationPermissions(
                allowed_capabilities=["knowledge", "artifacts", "notifications"],
                max_risk_level=RiskLevel.LOW_RISK,
            ),
        ),

        # 3. Daily Task Reminder
        Automation(
            id="tpl_daily_task_reminder",
            name="Daily Task Reminder",
            description="Remind user of high-priority due tasks every afternoon.",
            version=1,
            enabled=True,
            status=AutomationStatus.ACTIVE,
            scope=AutomationScope.GLOBAL,
            source=AutomationSource.TEMPLATE,
            trigger=TriggerConfig(
                type=TriggerType.SCHEDULE,
                schedule=TimeSchedule(
                    time_of_day="14:00",
                    days_of_week=["mon", "tue", "wed", "thu", "fri"],
                    timezone="Asia/Kolkata",
                ),
            ),
            steps=[
                AutomationStep(
                    step_id="s1",
                    name="Query High-Priority Tasks",
                    action="tasks.list_priority",
                    tool="tasks.list_pending",
                    input_template={"priority": "HIGH"},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s2",
                    name="Notify User",
                    action="notify_user",
                    tool="notifications.send",
                    input_template={"title": "High-Priority Tasks Reminder"},
                    risk_level=RiskLevel.SAFE,
                ),
            ],
            permissions=AutomationPermissions(
                allowed_capabilities=["tasks", "notifications"],
                max_risk_level=RiskLevel.SAFE,
            ),
        ),

        # 4. GitHub Issue Monitor
        Automation(
            id="tpl_github_issue_monitor",
            name="GitHub Issue Monitor",
            description="Check repository for new bug reports every hour and synthesize a digest.",
            version=1,
            enabled=True,
            status=AutomationStatus.ACTIVE,
            scope=AutomationScope.PROJECT,
            source=AutomationSource.TEMPLATE,
            trigger=TriggerConfig(
                type=TriggerType.INTERVAL,
                schedule=TimeSchedule(interval_seconds=3600),
            ),
            steps=[
                AutomationStep(
                    step_id="s1",
                    name="Fetch New Issues",
                    action="github.fetch_issues",
                    tool="github.read",
                    input_template={"state": "open", "labels": ["bug"]},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s2",
                    name="Notify on New Issues",
                    action="notify_user",
                    tool="notifications.send",
                    input_template={"title": "New GitHub Bug Reports"},
                    risk_level=RiskLevel.SAFE,
                ),
            ],
            permissions=AutomationPermissions(
                allowed_capabilities=["github", "notifications"],
                max_risk_level=RiskLevel.SAFE,
            ),
        ),

        # 5. Build Failure Analyzer
        Automation(
            id="tpl_build_failure_analyzer",
            name="Build Failure Analyzer",
            description="Triggered when a local test/build fails. Collects error logs and prepares suggested fix.",
            version=1,
            enabled=True,
            status=AutomationStatus.ACTIVE,
            scope=AutomationScope.PROJECT,
            source=AutomationSource.TEMPLATE,
            trigger=TriggerConfig(
                type=TriggerType.EVENT,
                event={"event_type": "TOOL_FAILED", "filter_expression": {"tool": "terminal_execute"}},
            ),
            steps=[
                AutomationStep(
                    step_id="s1",
                    name="Analyze Build Error Log",
                    action="code.inspect_error",
                    tool="code.inspect",
                    input_template={"error_source": "terminal"},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s2",
                    name="Draft Fix Patch (Requires User Review)",
                    action="code.prepare_patch",
                    tool="code.patch",
                    input_template={},
                    requires_approval=True,
                    risk_level=RiskLevel.HIGH_RISK,
                ),
            ],
            permissions=AutomationPermissions(
                allowed_capabilities=["code", "terminal", "notifications"],
                max_risk_level=RiskLevel.HIGH_RISK,
            ),
        ),

        # 6. Research Digest
        Automation(
            id="tpl_research_digest",
            name="Research Digest",
            description="Weekly automated literature and preprint scan on Artificial Intelligence.",
            version=1,
            enabled=True,
            status=AutomationStatus.ACTIVE,
            scope=AutomationScope.GLOBAL,
            source=AutomationSource.TEMPLATE,
            trigger=TriggerConfig(
                type=TriggerType.SCHEDULE,
                schedule=TimeSchedule(
                    time_of_day="10:00",
                    days_of_week=["fri"],
                    timezone="Asia/Kolkata",
                ),
            ),
            steps=[
                AutomationStep(
                    step_id="s1",
                    name="Scan arXiv and Web Sources",
                    action="research.search",
                    tool="research.search",
                    input_template={"query": "Autonomous AI Agents", "max_results": 5},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s2",
                    name="Synthesize Findings with Citations",
                    action="research.summarize",
                    tool="research.summarize",
                    input_template={"topic": "Autonomous AI Agents"},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s3",
                    name="Save Research Report",
                    action="research.save",
                    tool="research.save",
                    input_template={"query": "Autonomous AI Agents"},
                    risk_level=RiskLevel.LOW_RISK,
                ),
            ],
            permissions=AutomationPermissions(
                allowed_capabilities=["research", "artifacts", "notifications"],
                max_risk_level=RiskLevel.LOW_RISK,
            ),
        ),

        # 7. Device Connection Workflow
        Automation(
            id="tpl_device_connection",
            name="Device Connection Workflow",
            description="When Android phone connects, send desktop status heartbeat and sync unread notifications.",
            version=1,
            enabled=True,
            status=AutomationStatus.ACTIVE,
            scope=AutomationScope.DEVICE,
            source=AutomationSource.TEMPLATE,
            trigger=TriggerConfig(
                type=TriggerType.DEVICE,
                device_id="*",
            ),
            steps=[
                AutomationStep(
                    step_id="s1",
                    name="Send Online Notification to Phone",
                    action="phone.notify",
                    tool="android.notify",
                    input_template={"title": "SHIVANI Connected", "message": "Workstation is online."},
                    risk_level=RiskLevel.LOW_RISK,
                )
            ],
            permissions=AutomationPermissions(
                allowed_capabilities=["android", "notifications"],
                max_risk_level=RiskLevel.LOW_RISK,
            ),
        ),
    ]
