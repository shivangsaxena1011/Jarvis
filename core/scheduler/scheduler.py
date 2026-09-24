"""
SHIVANI Proactive Scheduler Service
Schedules non-invasive background workflows and periodic tasks with
interval controls, idempotency guards, and execution budgeting.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import threading
from typing import Any, Callable, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class ScheduleType(str, Enum):
    INTERVAL = "interval"
    ONCE = "once"


class ScheduledJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    prompt: str
    schedule_type: ScheduleType = ScheduleType.INTERVAL
    interval_seconds: int = 3600
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: Optional[str] = None
    idempotency_hash: Optional[str] = None
    max_runs: Optional[int] = None
    run_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_due(self, now: Optional[datetime] = None) -> bool:
        if not self.enabled:
            return False
        if self.max_runs is not None and self.run_count >= self.max_runs:
            return False
        if not self.next_run:
            return True
        current = now or datetime.now(timezone.utc)
        return current >= self.next_run


class SchedulerService:
    def __init__(self):
        self._jobs: Dict[str, ScheduledJob] = {}
        self._lock = threading.Lock()

    def schedule_job(
        self,
        name: str,
        prompt: str,
        interval_seconds: int = 3600,
        schedule_type: ScheduleType = ScheduleType.INTERVAL,
        run_immediately: bool = False,
        max_runs: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScheduledJob:
        now = datetime.now(timezone.utc)
        next_run = now if run_immediately else now + timedelta(seconds=interval_seconds)
        job = ScheduledJob(
            name=name,
            prompt=prompt,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            next_run=next_run,
            max_runs=max_runs,
            metadata=metadata or {},
        )
        with self._lock:
            self._jobs[job.id] = job
        return job

    def list_jobs(self) -> List[ScheduledJob]:
        with self._lock:
            return list(self._jobs.values())

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False

    def toggle_job(self, job_id: str, enabled: bool) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.enabled = enabled
                return True
            return False

    def check_idempotency(self, job_id: str, state_content: str) -> bool:
        """
        Calculates SHA-256 hash of external state.
        Returns True if state is identical to last run (already executed, skip side effect!).
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            curr_hash = hashlib.sha256(state_content.encode("utf-8")).hexdigest()
            if job.idempotency_hash == curr_hash:
                return True
            job.idempotency_hash = curr_hash
            return False

    async def execute_due(self, runner_callback: Callable[[str], Any]) -> List[str]:
        """Checks and runs all due scheduled jobs using the provided runner callback."""
        now = datetime.now(timezone.utc)
        due_jobs: List[ScheduledJob] = []

        with self._lock:
            for job in self._jobs.values():
                if job.is_due(now):
                    due_jobs.append(job)

        executed_job_ids: List[str] = []
        for job in due_jobs:
            try:
                res = runner_callback(job.prompt)
                if hasattr(res, "__await__"):
                    await res
                with self._lock:
                    job.last_run = now
                    job.run_count += 1
                    job.last_status = "success"
                    if job.schedule_type == ScheduleType.ONCE or (job.max_runs and job.run_count >= job.max_runs):
                        job.enabled = False
                    else:
                        job.next_run = now + timedelta(seconds=job.interval_seconds)
                executed_job_ids.append(job.id)
            except Exception as e:
                with self._lock:
                    job.last_run = now
                    job.last_status = f"failed: {e}"
                    job.next_run = now + timedelta(seconds=job.interval_seconds)

        return executed_job_ids
