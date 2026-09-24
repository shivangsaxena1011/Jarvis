"""
Unit tests for Phase 15 Time Triggers, Cron, Interval, and Timezone Scheduling.
"""

from datetime import datetime, timedelta, timezone
import pytest

from core.automation.models import (
    Automation,
    TimeSchedule,
    TriggerConfig,
    TriggerType,
)
from core.automation.triggers import TimeTriggerEvaluator


def test_timezone_resolution():
    tz = TimeTriggerEvaluator.get_tz("Asia/Kolkata")
    assert tz is not None


def test_interval_schedule_next_run():
    now = datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)
    schedule = TimeSchedule(interval_seconds=1800, timezone="Asia/Kolkata")
    next_run = TimeTriggerEvaluator.calculate_next_run(schedule, from_time=now)

    assert next_run is not None
    assert next_run == now + timedelta(seconds=1800)


def test_one_time_scheduled_task():
    future_time = datetime.now(timezone.utc) + timedelta(hours=2)
    schedule = TimeSchedule(specific_datetime=future_time.isoformat(), timezone="UTC")
    next_run = TimeTriggerEvaluator.calculate_next_run(schedule)

    assert next_run is not None
    assert abs((next_run - future_time).total_seconds()) < 5


def test_daily_time_of_day_schedule():
    tz = TimeTriggerEvaluator.get_tz("Asia/Kolkata")
    base_now = datetime(2026, 9, 24, 7, 0, 0, tzinfo=tz).astimezone(timezone.utc)
    schedule = TimeSchedule(
        time_of_day="08:00",
        days_of_week=["mon", "tue", "wed", "thu", "fri"],
        timezone="Asia/Kolkata",
    )
    next_run = TimeTriggerEvaluator.calculate_next_run(schedule, from_time=base_now)

    assert next_run is not None
    local_next = next_run.astimezone(tz)
    assert local_next.hour == 8
    assert local_next.minute == 0


def test_cron_syntax_evaluation():
    tz = TimeTriggerEvaluator.get_tz("Asia/Kolkata")
    base_now = datetime(2026, 9, 24, 7, 30, 0, tzinfo=tz).astimezone(timezone.utc)
    # Cron: Every day at 8:00 AM -> "0 8 * * *"
    schedule = TimeSchedule(cron="0 8 * * *", timezone="Asia/Kolkata")
    next_run = TimeTriggerEvaluator.calculate_next_run(schedule, from_time=base_now)

    assert next_run is not None
    local_next = next_run.astimezone(tz)
    assert local_next.hour == 8
    assert local_next.minute == 0


def test_is_due_and_max_executions():
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    auto = Automation(
        name="Test Once",
        trigger=TriggerConfig(
            type=TriggerType.ONCE,
            schedule=TimeSchedule(max_executions=1),
        ),
        next_run=past_time,
        run_count=0,
    )

    due, reason = TimeTriggerEvaluator.is_due(auto)
    assert due is True

    # After running max_executions reached
    auto.run_count = 1
    due_after, reason_after = TimeTriggerEvaluator.is_due(auto)
    assert due_after is False
    assert "Maximum executions reached" in reason_after
