"""
SHIVANI Dependency Engine (Phase 16).
Manages task and milestone dependency DAGs, detects cycles, orphaned tasks,
and computes transitive blocker propagation.
"""

from typing import Dict, List, Set, Tuple
from core.productivity.models import PersonalTask, TaskStatus


class DependencyEngine:
    """Evaluates task dependencies, validates DAG integrity, and resolves blocked states."""

    @staticmethod
    def build_adj_list(tasks: List[PersonalTask]) -> Dict[str, List[str]]:
        """Builds directed adjacency list: task_id -> list of prerequisite task_ids."""
        adj: Dict[str, List[str]] = {}
        for t in tasks:
            adj[t.id] = list(t.dependencies)
        return adj

    @classmethod
    def detect_cycles(cls, tasks: List[PersonalTask]) -> List[List[str]]:
        """
        Detects circular dependencies in task relationships.
        Returns list of cycle paths if any are found.
        """
        adj = cls.build_adj_list(tasks)
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
        cycles: List[List[str]] = []

        def dfs(node: str, path: List[str]):
            visited[node] = 1
            path.append(node)

            for prereq in adj.get(node, []):
                if prereq not in visited or visited[prereq] == 0:
                    dfs(prereq, path)
                elif visited[prereq] == 1:
                    # Found cycle
                    cycle_start_idx = path.index(prereq)
                    cycles.append(path[cycle_start_idx:] + [prereq])

            path.pop()
            visited[node] = 2

        for task_id in adj:
            if visited.get(task_id, 0) == 0:
                dfs(task_id, [])

        return cycles

    @classmethod
    def get_blocked_status(
        cls,
        task: PersonalTask,
        all_tasks: Dict[str, PersonalTask],
    ) -> Tuple[bool, List[str]]:
        """
        Determines if a task is blocked by incomplete dependencies.
        Returns (is_blocked, list_of_blocking_task_titles_or_ids).
        """
        if not task.dependencies:
            return False, []

        blocking_reasons: List[str] = []
        for dep_id in task.dependencies:
            dep_task = all_tasks.get(dep_id)
            if not dep_task:
                blocking_reasons.append(f"Missing dependency task (ID: {dep_id})")
            elif dep_task.status != TaskStatus.COMPLETED:
                blocking_reasons.append(f"Waiting for '{dep_task.title}' (Status: {dep_task.status.value})")

        return len(blocking_reasons) > 0, blocking_reasons

    @classmethod
    def topological_sort(cls, tasks: List[PersonalTask]) -> List[PersonalTask]:
        """
        Sorts tasks in executable order such that dependencies precede dependents.
        Falls back to original order if circular dependencies are present.
        """
        task_map = {t.id: t for t in tasks}
        adj = cls.build_adj_list(tasks)
        in_degree: Dict[str, int] = {t.id: 0 for t in tasks}

        for node, prereqs in adj.items():
            for p in prereqs:
                if p in in_degree:
                    in_degree[node] += 1

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        sorted_ids: List[str] = []

        while queue:
            curr = queue.pop(0)
            sorted_ids.append(curr)

            for node, prereqs in adj.items():
                if curr in prereqs and node in in_degree:
                    in_degree[node] -= 1
                    if in_degree[node] == 0:
                        queue.append(node)

        if len(sorted_ids) != len(tasks):
            # Circular dependency detected, return original tasks list
            return tasks

        return [task_map[tid] for tid in sorted_ids if tid in task_map]
