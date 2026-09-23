"""
SHIVANI Action Executor
Executes planned steps sequentially with OBSERVE -> PLAN -> ACT -> VERIFY discipline,
observing emergency cancellation checks and real-time step streaming.
"""

import asyncio
from typing import Callable, Optional
from core.orchestrator.state_machine import Task, TaskState, StepExecutionResult
from core.orchestrator.emergency import EmergencyStop
from tools.registry import ToolRegistry


class TaskExecutor:
    def __init__(self, tool_registry: ToolRegistry, emergency_stop: EmergencyStop):
        self.tools = tool_registry
        self.emergency = emergency_stop

    async def execute_task(
        self,
        task: Task,
        on_step_update: Optional[Callable[[Task, str], None]] = None
    ) -> Task:
        if not task.plan or not task.plan.steps:
            task.transition_to(TaskState.COMPLETED, "Plan contained 0 steps; nothing to execute.")
            task.final_output = "No action was required."
            return task

        task.transition_to(TaskState.EXECUTING, f"Starting execution of {len(task.plan.steps)} steps.")

        for idx, step in enumerate(task.plan.steps):
            task.current_step_index = idx

            # 1. Check for Emergency Cancellation
            if self.emergency.is_task_cancelled(task.id):
                task.transition_to(TaskState.CANCELLED, "Execution stopped by Emergency Stop signal.")
                task.error = "Emergency Stop Aborted Active Task"
                return task

            # Broadcast step progress
            step_msg = f"Step {idx + 1}/{len(task.plan.steps)}: {step.action}"
            if on_step_update:
                on_step_update(task, step_msg)

            # 2. ACT: Execute Tool via Registry
            tool_res = await self.tools.execute_tool(
                name=step.tool,
                arguments=step.arguments,
                task_id=task.id
            )

            # 3. VERIFY: Record and inspect verification
            task.transition_to(TaskState.VERIFYING, f"Verifying outcome of step {idx + 1}: {step.action}")
            
            step_record = StepExecutionResult(
                step_id=step.id,
                tool=step.tool,
                action=step.action,
                arguments=step.arguments,
                success=tool_res.success,
                data=tool_res.data,
                verification=tool_res.verification,
                error=tool_res.error,
                execution_time_ms=tool_res.execution_time_ms
            )
            task.step_results.append(step_record)

            if not tool_res.success:
                task.transition_to(
                    TaskState.FAILED,
                    f"Step {idx + 1} failed: {tool_res.error}",
                    details={"failed_step": step.model_dump()}
                )
                task.error = f"Step '{step.action}' failed: {tool_res.error}"
                return task

        # All steps executed and verified successfully
        task.transition_to(TaskState.COMPLETED, "All task steps completed and verified successfully.")
        task.final_output = f"Successfully completed: {task.plan.goal}"
        return task
