"""
SHIVANI Plan Serializer.
Serializes and deserializes Goals and TaskGraphs to/from JSON with execution state preservation.
"""

from typing import Dict, Any, Tuple
import json
from pathlib import Path
from planning.models import Goal, SubTaskPlan
from planning.dependency_graph import TaskGraph


class PlanSerializer:
    """Serializes Goals and TaskGraphs for persistent checkpoints and wire transport."""

    @classmethod
    def serialize_to_dict(cls, goal: Goal, graph: TaskGraph) -> Dict[str, Any]:
        """Converts Goal and TaskGraph into a serializable JSON-compatible dictionary."""
        return {
            "goal": goal.model_dump(),
            "nodes": [node.subtask.model_dump() for node in graph.nodes.values()],
            "edges": graph.edges,
        }

    @classmethod
    def deserialize_from_dict(cls, data: Dict[str, Any]) -> Tuple[Goal, TaskGraph]:
        """Reconstructs Goal and TaskGraph from serialized dictionary."""
        goal = Goal(**data["goal"])
        graph = TaskGraph()

        # Add all nodes
        for node_dict in data.get("nodes", []):
            st = SubTaskPlan(**node_dict)
            graph.add_node(st)

        # Wire all edges
        for from_id, to_id in data.get("edges", []):
            if from_id in graph.nodes and to_id in graph.nodes:
                graph.nodes[from_id].successors.add(to_id)
                graph.nodes[to_id].predecessors.add(from_id)
                if (from_id, to_id) not in graph.edges:
                    graph.edges.append((from_id, to_id))

        return (goal, graph)

    @classmethod
    def save_to_json(cls, goal: Goal, graph: TaskGraph, file_path: str) -> None:
        """Saves plan state to JSON file."""
        data = cls.serialize_to_dict(goal, graph)
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, file_path: str) -> Tuple[Goal, TaskGraph]:
        """Loads plan state from JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.deserialize_from_dict(data)
