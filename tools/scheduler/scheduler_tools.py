"""
SHIVANI Scheduler Tools
Registered tools for inspecting, scheduling, and cancelling proactive scheduled workflows.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from core.scheduler.scheduler import SchedulerService


class SchedulerListJobsArgs(BaseModel):
    pass


class SchedulerListJobsTool(BaseTool):
    name = "scheduler.list_jobs"
    description = "Lists all proactive background scheduled workflows and jobs."
    permission_level = RiskLevel.SAFE
    args_schema = SchedulerListJobsArgs
    timeout = 10.0

    def __init__(self, scheduler: Optional[SchedulerService] = None):
        super().__init__()
        self.scheduler = scheduler or SchedulerService()

    async def run(self) -> Dict[str, Any]:
        jobs = self.scheduler.list_jobs()
        return {
            "count": len(jobs),
            "jobs": [j.model_dump() for j in jobs],
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": isinstance(result_data.get("jobs"), list)}


class SchedulerScheduleJobArgs(BaseModel):
    name: str = Field(description="Descriptive job name, e.g. 'Daily repo sync'")
    prompt: str = Field(description="Natural language instruction or workflow to trigger")
    interval_seconds: int = Field(default=3600, description="Repeat interval in seconds (default 1 hour)")
    run_immediately: bool = Field(default=False, description="Whether to execute immediately upon scheduling")
    max_runs: Optional[int] = Field(default=None, description="Optional maximum number of runs")


class SchedulerScheduleJobTool(BaseTool):
    name = "scheduler.schedule_job"
    description = "Schedules a recurring or delayed background workflow."
    permission_level = RiskLevel.SAFE
    args_schema = SchedulerScheduleJobArgs
    timeout = 10.0

    def __init__(self, scheduler: Optional[SchedulerService] = None):
        super().__init__()
        self.scheduler = scheduler or SchedulerService()

    async def run(
        self,
        name: str,
        prompt: str,
        interval_seconds: int = 3600,
        run_immediately: bool = False,
        max_runs: Optional[int] = None,
    ) -> Dict[str, Any]:
        job = self.scheduler.schedule_job(
            name=name,
            prompt=prompt,
            interval_seconds=interval_seconds,
            run_immediately=run_immediately,
            max_runs=max_runs,
        )
        return {"status": "scheduled", "job": job.model_dump()}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("job", {}).get("id"))}


class SchedulerCancelJobArgs(BaseModel):
    job_id: str = Field(description="ID of the scheduled job to cancel")


class SchedulerCancelJobTool(BaseTool):
    name = "scheduler.cancel_job"
    description = "Cancels a scheduled background workflow by its ID."
    permission_level = RiskLevel.SAFE
    args_schema = SchedulerCancelJobArgs
    timeout = 10.0

    def __init__(self, scheduler: Optional[SchedulerService] = None):
        super().__init__()
        self.scheduler = scheduler or SchedulerService()

    async def run(self, job_id: str) -> Dict[str, Any]:
        cancelled = self.scheduler.cancel_job(job_id)
        return {"cancelled": cancelled, "job_id": job_id}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("cancelled"))}
