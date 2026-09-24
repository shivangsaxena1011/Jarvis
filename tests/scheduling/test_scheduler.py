"""
SHIVANI Proactive Scheduler & Notification Center Test Suite
Verifies:
- Notification Center prioritization and listener dispatch
- SchedulerService interval jobs, due evaluation, and execution
- Idempotency guard skipping duplicate side-effects
- Scheduler & Notification registered tools
"""

import pytest
from notifications.center import NotificationCenter, NotificationCategory
from core.scheduler.scheduler import SchedulerService, ScheduleType
from tools.scheduler import (
    SchedulerListJobsTool,
    SchedulerScheduleJobTool,
    SchedulerCancelJobTool,
)
from tools.notifications import (
    NotificationsListTool,
    NotificationsDismissTool,
)


def test_notification_center_categories_and_listeners():
    center = NotificationCenter()
    received_items = []

    center.subscribe(lambda item: received_items.append(item))

    n1 = center.notify("Welcome", "Shivani system started", NotificationCategory.INFO)
    n2 = center.notify("Approval Needed", "Publish to LinkedIn?", NotificationCategory.ACTION_REQUIRED)

    assert len(received_items) == 2
    assert center.get_unread_count() == 2

    # Query ACTION_REQUIRED category
    actions = center.list_notifications(category=NotificationCategory.ACTION_REQUIRED)
    assert len(actions) == 1
    assert actions[0].title == "Approval Needed"

    # Mark as read
    center.mark_as_read(n1.id)
    assert center.get_unread_count() == 1

    # Dismiss
    dismissed = center.dismiss(n2.id)
    assert dismissed is True
    assert center.get_unread_count() == 0


@pytest.mark.asyncio
async def test_scheduler_service_execution_and_idempotency():
    scheduler = SchedulerService()

    executed_prompts = []
    async def dummy_runner(prompt: str):
        executed_prompts.append(prompt)

    # 1. Schedule immediate job
    job = scheduler.schedule_job(
        name="Test Immediate Task",
        prompt="Sync git repositories",
        interval_seconds=60,
        run_immediately=True,
    )
    assert job.is_due() is True

    # Execute due jobs
    executed_ids = await scheduler.execute_due(dummy_runner)
    assert job.id in executed_ids
    assert len(executed_prompts) == 1
    assert executed_prompts[0] == "Sync git repositories"

    # Job is no longer due immediately
    assert job.is_due() is False

    # 2. Idempotency test: verify state before repeating external side effect
    state_a = "Commit 12345: Auth fixed"
    assert scheduler.check_idempotency(job.id, state_a) is False # First time: not duplicate
    assert scheduler.check_idempotency(job.id, state_a) is True  # Second time with same content: duplicate!


@pytest.mark.asyncio
async def test_scheduler_and_notification_tools():
    center = NotificationCenter()
    scheduler = SchedulerService()

    list_notif_tool = NotificationsListTool(notification_center=center)
    dismiss_notif_tool = NotificationsDismissTool(notification_center=center)

    list_jobs_tool = SchedulerListJobsTool(scheduler=scheduler)
    schedule_job_tool = SchedulerScheduleJobTool(scheduler=scheduler)
    cancel_job_tool = SchedulerCancelJobTool(scheduler=scheduler)

    # Schedule a job via tool
    res_sched = await schedule_job_tool.run(
        name="Backup logs",
        prompt="Archive audit logs to disk",
        interval_seconds=300,
    )
    assert res_sched["status"] == "scheduled"
    job_id = res_sched["job"]["id"]

    # List jobs via tool
    res_list = await list_jobs_tool.run()
    assert res_list["count"] == 1
    assert res_list["jobs"][0]["name"] == "Backup logs"

    # Cancel job via tool
    res_cancel = await cancel_job_tool.run(job_id=job_id)
    assert res_cancel["cancelled"] is True
    res_list_after = await list_jobs_tool.run()
    assert res_list_after["count"] == 0

    # Notification tools
    n = center.notify("Test Alert", "Verification successful", NotificationCategory.SUCCESS)
    notif_list_res = await list_notif_tool.run()
    assert notif_list_res["count"] == 1

    dismiss_res = await dismiss_notif_tool.run(notification_id=n.id)
    assert dismiss_res["dismissed"] is True
    notif_list_after = await list_notif_tool.run()
    assert notif_list_after["count"] == 0
