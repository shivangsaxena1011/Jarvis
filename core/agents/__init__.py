"""
SHIVANI Multi-Agent Coordination Package
"""

from core.agents.communication import AgentMessage, AgentMessageType, AgentResponse
from core.agents.registry import AgentDescriptor, AgentRegistry
from core.agents.decomposer import TaskDecomposer, TaskDAG, SubTask, TaskStage

__all__ = [
    "AgentMessage",
    "AgentMessageType",
    "AgentResponse",
    "AgentDescriptor",
    "AgentRegistry",
    "TaskDecomposer",
    "TaskDAG",
    "SubTask",
    "TaskStage",
]
