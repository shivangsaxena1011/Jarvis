"""
SHIVANI Action Executor
Executes planned steps with OBSERVE -> PLAN -> ACT -> VERIFY discipline,
emits granular event bus notifications, and attempts rollback on failure.
"""

from typing import Callable, Optional
from core.tasks.task import Task, TaskStatus, StepExecutionResult
from core.orchestrator.emergency import EmergencyStop
from core.events.bus import EventBus, EventType, get_event_bus
from tools.registry import ToolRegistry


class TaskExecutor:
    def __init__(
        self,
        tool_registry: ToolRegistry,
        emergency_stop: EmergencyStop,
        event_bus: Optional[EventBus] = None
    ):
        self.tools = tool_registry
        self.emergency = emergency_stop
        self.events = event_bus or get_event_bus()

    async def execute_task(
        self,
        task: Task,
        on_step_update: Optional[Callable[[Task, str], None]] = None
    ) -> Task:
        if not task.plan or not task.plan.steps:
            task.transition_to(TaskStatus.COMPLETED, "Plan contained 0 steps; nothing to execute.")
            task.result = "No action was required."
            self.events.publish(EventType.TASK_COMPLETED, task_id=task.id, data={"task": task.model_dump()})
            return task

        task.transition_to(TaskStatus.EXECUTING, f"Starting execution of {len(task.plan.steps)} steps.")
        self.events.publish(EventType.TASK_STARTED, task_id=task.id, data={"step_count": len(task.plan.steps)})

        for idx, step in enumerate(task.plan.steps):
            task.current_step = idx

            # 1. Check for Emergency Cancellation
            if self.emergency.is_task_cancelled(task.id):
                task.transition_to(TaskStatus.CANCELLED, "Execution aborted by Emergency Stop.")
                task.error = "Emergency Stop Aborted Active Task"
                self.events.publish(EventType.TASK_CANCELLED, task_id=task.id, data={"reason": "Emergency Stop"})
                return task

            step_msg = f"Step {idx + 1}/{len(task.plan.steps)}: {step.action}"
            if on_step_update:
                on_step_update(task, step_msg)

            # 2. ACT: Tool Execution
            self.events.publish(EventType.TOOL_STARTED, task_id=task.id, data={"step_id": step.id, "tool": step.tool, "action": step.action})
            tool_res = await self.tools.execute_tool(
                name=step.tool,
                arguments=step.arguments,
                task_id=task.id
            )

            # 3. VERIFY
            task.transition_to(TaskStatus.VERIFYING, f"Verifying step {idx + 1}: {step.action}")
            self.events.publish(EventType.TASK_VERIFYING, task_id=task.id, data={"step_id": step.id, "tool": step.tool})

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
                self.events.publish(EventType.TOOL_FAILED, task_id=task.id, data={"step_id": step.id, "error": tool_res.error})
                
                # Attempt rollback if supported by tool
                tool_instance = self.tools.get_tool(step.tool)
                if tool_instance:
                    try:
                        rolled_back = await tool_instance.rollback_if_possible(**step.arguments)
                        if rolled_back:
                            step_record.verification["rolled_back"] = True
                    except Exception:
                        pass

                task.transition_to(
                    TaskStatus.FAILED,
                    f"Step {idx + 1} failed: {tool_res.error}",
                    details={"failed_step": step.model_dump()}
                )
                task.error = f"Step '{step.action}' failed: {tool_res.error}"
                self.events.publish(EventType.TASK_FAILED, task_id=task.id, data={"error": task.error})
                return task

            self.events.publish(EventType.TOOL_COMPLETED, task_id=task.id, data={"step_id": step.id, "verification": tool_res.verification})

        # All steps completed and verified
        task.transition_to(TaskStatus.COMPLETED, "All steps completed and verified successfully.")
        task.result = f"Successfully completed: {task.plan.goal}"
        self.events.publish(EventType.TASK_COMPLETED, task_id=task.id, data={"result": task.result})
        return task
