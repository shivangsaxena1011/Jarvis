"""
SHIVANI Dynamic Replanner & Self-Correction Engine.
Diagnoses execution failures, synthesizes corrective fallback paths, and updates TaskGraph in-flight.
"""

from typing import Tuple, Optional, Dict, Any
from planning.models import SubTaskPlan, TaskNode, SubTaskStatus, ReplanTrigger
from planning.dependency_graph import TaskGraph


class Replanner:
    """Diagnoses task failures and adapts the execution graph dynamically."""

    def diagnose_failure(self, node: TaskNode, error_message: str) -> ReplanTrigger:
        """Classifies the root cause of an execution failure."""
        err_lower = error_message.lower()

        error_type = "EXECUTION_ERROR"
        diagnosis = "Generic execution error encountered."
        suggested_action = "RETRY"

        if any(w in err_lower for w in ["timeout", "timed out", "deadline exceeded"]):
            error_type = "TIMEOUT"
            diagnosis = "Operation exceeded allotted timeout duration."
            suggested_action = "EXPAND_TIMEOUT_AND_RETRY"

        elif any(w in err_lower for w in ["permission denied", "rejected by user", "unauthorized"]):
            error_type = "PERMISSION_DENIED"
            diagnosis = "Action prohibited by security policy or rejected by user."
            suggested_action = "SKIP_OR_ABORT"

        elif any(w in err_lower for w in ["visual", "not found on screen", "could not locate", "ocr"]):
            error_type = "VISUAL_MISMATCH"
            diagnosis = "GUI control was not visually groundable on current screen."
            suggested_action = "FALLBACK_TO_KEYBOARD_NAVIGATION"

        elif any(w in err_lower for w in ["connection refused", "network", "blocked", "http 403", "captcha"]):
            error_type = "TOOL_FAILURE"
            diagnosis = "External network or web scraping request failed."
            suggested_action = "SYNTHESIZE_ALTERNATIVE_SOURCE"

        elif any(w in err_lower for w in ["file not found", "no such file", "missing input"]):
            error_type = "INPUT_MISSING"
            diagnosis = "Preceding task output artifact was missing or unreadable."
            suggested_action = "REGENERATE_INPUT"

        return ReplanTrigger(
            failed_node_id=node.subtask.id,
            failure_reason=error_message,
            error_type=error_type,
            diagnosis=diagnosis,
            suggested_action=suggested_action,
        )

    def replan(self, graph: TaskGraph, trigger: ReplanTrigger) -> Tuple[TaskGraph, bool]:
        """
        Dynamically modifies the TaskGraph to recover from failure.
        Returns: (revised_graph, can_continue)
        """
        if trigger.failed_node_id not in graph.nodes:
            return (graph, False)

        failed_node = graph.nodes[trigger.failed_node_id]

        # Strategy 1: Expand timeout and retry if timeout error
        if trigger.error_type == "TIMEOUT":
            curr_retries = failed_node.subtask.retry_policy.get("max_retries", 1)
            if curr_retries > 0:
                failed_node.subtask.retry_policy["max_retries"] = curr_retries - 1
                failed_node.subtask.timeout_seconds *= 2.0
                failed_node.subtask.status = SubTaskStatus.PENDING
                failed_node.subtask.error = None
                return (graph, True)

        # Strategy 2: Synthesize alternative fallback tool/subtask on TOOL_FAILURE or VISUAL_MISMATCH
        if trigger.error_type in ("TOOL_FAILURE", "VISUAL_MISMATCH"):
            # Create a fallback node
            fallback_subtask = SubTaskPlan(
                title=f"Fallback: {failed_node.subtask.title}",
                description=f"Alternative execution path for {failed_node.subtask.title} using heuristic fallback.",
                assigned_agent=(
                    "coding_agent"
                    if failed_node.subtask.assigned_agent == "research_agent"
                    else "computer_agent"
                ),
                stage=failed_node.subtask.stage,
                inputs=failed_node.subtask.inputs,
                outputs=failed_node.subtask.outputs,
                dependencies=list(failed_node.predecessors),
                risk_level=failed_node.subtask.risk_level,
                expected_result=f"Synthesized fallback result for {failed_node.subtask.outputs}",
            )
            fallback_node = graph.add_node(fallback_subtask)

            # Rewire successors of failed node to depend on fallback node instead
            for succ_id in list(failed_node.successors):
                graph.nodes[succ_id].predecessors.remove(failed_node.subtask.id)
                graph.nodes[succ_id].subtask.dependencies.remove(failed_node.subtask.id)
                graph.nodes[succ_id].predecessors.add(fallback_node.subtask.id)
                graph.nodes[succ_id].subtask.dependencies.append(fallback_node.subtask.id)
                fallback_node.successors.add(succ_id)

            failed_node.successors.clear()
            failed_node.subtask.status = SubTaskStatus.SKIPPED

            return (graph, True)

        # Strategy 3: Non-critical optional leaf node (e.g. social post or notification)
        if len(failed_node.successors) == 0:
            # Leaf node with no dependents: mark as skipped so parent goal can succeed
            failed_node.subtask.status = SubTaskStatus.SKIPPED
            failed_node.subtask.result_data = {"skipped": True, "reason": trigger.failure_reason}
            return (graph, True)

        # If critical and non-recoverable
        return (graph, False)
