"""
SHIVANI Advanced Planner Facade.
Unified entry point coordinating Goal Parsing, Task Decomposition, Dependency Graphing,
Priority Scheduling, Constraint Enforcement, Plan Validation, and Self-Correction Replanning.
"""

from typing import Optional, List, Tuple, Dict, Any
from planning.models import (
    Goal,
    TaskNode,
    ExecutionStrategy,
    PlanValidationResult,
    ReplanTrigger,
)
from planning.goal_parser import GoalParser
from planning.task_decomposer import HierarchicalTaskDecomposer
from planning.dependency_graph import TaskGraph
from planning.priority_engine import PriorityEngine
from planning.strategy_selector import StrategySelector
from planning.constraint_engine import ConstraintEngine
from planning.plan_validator import PlanValidator
from planning.replanner import Replanner
from planning.plan_serializer import PlanSerializer
from memory.manager import MemoryManager


class AdvancedPlanner:
    """Production agentic planner orchestrating the complete Phase 11 planning pipeline."""

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory = memory_manager
        self.parser = GoalParser(self.memory)
        self.decomposer = HierarchicalTaskDecomposer()
        self.priority_engine = PriorityEngine()
        self.strategy_selector = StrategySelector()
        self.constraint_engine = ConstraintEngine()
        self.validator = PlanValidator()
        self.replanner = Replanner()
        self.serializer = PlanSerializer()

    def create_plan_for_goal(
        self,
        query: str,
        available_agents: Optional[List[str]] = None,
    ) -> Tuple[Goal, TaskGraph, ExecutionStrategy, PlanValidationResult]:
        """
        Executes full planning pipeline:
        Parse -> Clarify -> Decompose -> Graph -> Prioritize -> Strategy -> Constraints -> Validate
        """
        # 1. Goal Parsing & Clarification Check
        goal = self.parser.parse(query)
        graph = TaskGraph()

        if goal.needs_clarification:
            return (
                goal,
                graph,
                ExecutionStrategy.SEQUENTIAL,
                PlanValidationResult(
                    is_valid=False,
                    errors=[f"Goal requires user clarification: {goal.clarification_question}"],
                ),
            )

        # 2. Hierarchical Task Decomposition
        subtasks = self.decomposer.decompose(goal)

        # 3. Construct Dependency Graph (DAG)
        for st in subtasks:
            graph.add_node(st)

        # 4. Priority Calculation & Critical Path Identification
        self.priority_engine.calculate_priorities(graph)

        # 5. Execution Strategy Selection
        strategy = self.strategy_selector.select_strategy(goal, graph)

        # 6. Constraint Enforcement
        constraint_ok, violations = self.constraint_engine.validate_constraints(
            goal=goal,
            graph=graph,
            available_agents=available_agents,
        )

        # 7. Plan Soundness Validation
        validation = self.validator.validate(graph)
        if not constraint_ok:
            validation.is_valid = False
            validation.errors.extend(violations)

        return (goal, graph, strategy, validation)

    def replan_on_failure(
        self,
        graph: TaskGraph,
        node_id: str,
        error_message: str,
    ) -> Tuple[TaskGraph, bool, ReplanTrigger]:
        """
        Diagnoses node execution failure and dynamically replans alternative route.
        Returns: (revised_graph, can_continue, trigger_diagnosis)
        """
        if node_id not in graph.nodes:
            raise KeyError(f"Node '{node_id}' not found in graph for replanning.")

        node = graph.nodes[node_id]
        trigger = self.replanner.diagnose_failure(node, error_message)
        revised_graph, can_continue = self.replanner.replan(graph, trigger)

        if can_continue:
            # Re-calculate priorities on adapted graph
            self.priority_engine.calculate_priorities(revised_graph)

        return (revised_graph, can_continue, trigger)


_global_advanced_planner: Optional[AdvancedPlanner] = None


def get_advanced_planner(memory_manager: Optional[MemoryManager] = None) -> AdvancedPlanner:
    """Global singleton accessor for AdvancedPlanner."""
    global _global_advanced_planner
    if _global_advanced_planner is None:
        _global_advanced_planner = AdvancedPlanner(memory_manager=memory_manager)
    return _global_advanced_planner
