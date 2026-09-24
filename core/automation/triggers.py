"""
SHIVANI Trigger System (Phase 15).
Timezone-aware Time Triggers (cron, interval, once, days-of-week) and Event-Based Triggers.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import re
from typing import Any, Dict, List, Optional, Tuple

from core.automation.models import Automation, TriggerConfig, TriggerType, TimeSchedule, EventFilter
from core.events.bus import Event, EventType


# Day-of-week abbreviations map (0 = Monday, 6 = Sunday)
DOW_MAP = {
    "mon": 0, "monday": 0,
    "tue": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}


class TimeTriggerEvaluator:
    """Calculates next run times and evaluates whether a time trigger is due."""

    @staticmethod
    def get_tz(tz_name: str) -> Any:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            try:
                return ZoneInfo("Asia/Kolkata")
            except Exception:
                if "kolkata" in tz_name.lower() or "india" in tz_name.lower() or "ist" in tz_name.lower():
                    return timezone(timedelta(hours=5, minutes=30))
                return timezone.utc

    @classmethod
    def calculate_next_run(cls, schedule: TimeSchedule, from_time: Optional[datetime] = None) -> Optional[datetime]:
        """Calculates the upcoming scheduled datetime given the current reference time."""
        tz = cls.get_tz(schedule.timezone)
        base_now = from_time or datetime.now(timezone.utc)
        local_now = base_now.astimezone(tz)

        # 1. One-time specific datetime
        if schedule.specific_datetime:
            dt = datetime.fromisoformat(schedule.specific_datetime)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            if dt > local_now:
                return dt.astimezone(timezone.utc)
            return None

        # 2. Interval seconds
        if schedule.interval_seconds and schedule.interval_seconds > 0:
            next_dt = local_now + timedelta(seconds=schedule.interval_seconds)
            return next_dt.astimezone(timezone.utc)

        # 3. Time of day + Days of week
        if schedule.time_of_day:
            try:
                hour, minute = map(int, schedule.time_of_day.split(":"))
            except Exception:
                hour, minute = 8, 0

            target_dows = [DOW_MAP[d.lower()] for d in schedule.days_of_week if d.lower() in DOW_MAP]

            # Search up to 14 days ahead for matching candidate
            for day_offset in range(15):
                candidate_date = (local_now + timedelta(days=day_offset)).date()
                candidate_dt = datetime(
                    candidate_date.year, candidate_date.month, candidate_date.day,
                    hour, minute, 0, tzinfo=tz
                )

                if candidate_dt <= local_now:
                    continue

                if not target_dows or candidate_dt.weekday() in target_dows:
                    return candidate_dt.astimezone(timezone.utc)

        # 4. Standard Cron string (min hour dom mon dow)
        if schedule.cron:
            return cls._next_cron_run(schedule.cron, local_now, tz)

        return None

    @classmethod
    def _next_cron_run(cls, cron_expr: str, local_now: datetime, tz: ZoneInfo) -> Optional[datetime]:
        """Evaluates standard 5-part cron syntax: minute hour dom month dow."""
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return local_now + timedelta(hours=1)

        c_min, c_hour, c_dom, c_mon, c_dow = parts

        def match_field(val: int, expr: str) -> bool:
            if expr == "*":
                return True
            if "/" in expr:
                sub, step = expr.split("/", 1)
                start = 0 if sub == "*" else int(sub)
                return (val - start) % int(step) == 0 and val >= start
            if "," in expr:
                return val in [int(x) for x in expr.split(",")]
            if "-" in expr:
                lo, hi = map(int, expr.split("-", 1))
                return lo <= val <= hi
            try:
                return val == int(expr)
            except ValueError:
                return False

        # Scan minute by minute up to 7 days
        curr = local_now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        max_scan_minutes = 7 * 24 * 60
        for _ in range(max_scan_minutes):
            if (
                match_field(curr.minute, c_min)
                and match_field(curr.hour, c_hour)
                and match_field(curr.day, c_dom)
                and match_field(curr.month, c_mon)
                and match_field(curr.weekday(), c_dow)
            ):
                return curr.astimezone(timezone.utc)
            curr += timedelta(minutes=1)

        return None

    @classmethod
    def is_due(cls, automation: Automation, now: Optional[datetime] = None) -> Tuple[bool, Optional[str]]:
        """Determines if the automation is due to run."""
        if not automation.enabled:
            return False, "Automation disabled"

        if not automation.next_run:
            return False, "No next run scheduled"

        curr_now = now or datetime.now(timezone.utc)
        next_dt = datetime.fromisoformat(automation.next_run)
        if next_dt.tzinfo is None:
            next_dt = next_dt.replace(tzinfo=timezone.utc)

        if curr_now >= next_dt:
            # Check maximum executions limit
            if (
                automation.trigger.schedule
                and automation.trigger.schedule.max_executions
                and automation.run_count >= automation.trigger.schedule.max_executions
            ):
                return False, "Maximum executions reached"
            return True, None

        return False, "Not due yet"


# ==============================================================================
# EVENT TRIGGER MATCHER
# ==============================================================================

class EventTriggerMatcher:
    """Matches incoming system and external events against automation event triggers."""

    @staticmethod
    def matches_event(trigger: TriggerConfig, event_type: str, event_data: Dict[str, Any]) -> bool:
        if trigger.type != TriggerType.EVENT or not trigger.event:
            return False

        # 1. Match Event Type
        if trigger.event.event_type != "*" and trigger.event.event_type.upper() != event_type.upper():
            return False

        # 2. Match Source if declared
        if trigger.event.source and event_data.get("source") != trigger.event.source:
            return False

        # 3. Match Filter Expressions (e.g. {"status": "FAILED", "label": "bug"})
        for k, v in trigger.event.filter_expression.items():
            actual = event_data.get(k)
            if actual != v:
                return False

        return True

    @staticmethod
    def matches_file_change(trigger: TriggerConfig, file_path: str, change_type: str = "created") -> bool:
        if trigger.type != TriggerType.FILE or not trigger.file_path:
            return False

        # Normalize paths
        watch_dir = trigger.file_path.replace("\\", "/").rstrip("/")
        target_path = file_path.replace("\\", "/")

        if not target_path.startswith(watch_dir):
            return False

        # Pattern check (e.g. *.pdf)
        filename = target_path.split("/")[-1].lower()
        for pat in trigger.file_patterns:
            if pat == "*":
                return True
            if pat.startswith("*.") and filename.endswith(pat[1:].lower()):
                return True
            if pat.lower() in filename:
                return True

        return False

    @staticmethod
    def matches_device_event(trigger: TriggerConfig, device_id: str, action: str = "connected") -> bool:
        if trigger.type != TriggerType.DEVICE:
            return False

        if trigger.device_id and trigger.device_id != "*" and trigger.device_id != device_id:
            return False

        return True
