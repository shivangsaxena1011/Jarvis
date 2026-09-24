"""
SHIVANI Task Decomposer
Breaks complex user goals into a Directed Acyclic Graph (DAG) of dependent sub-tasks
with stage checkpoints (RESEARCH, ARCHITECTURE, IMPLEMENTATION, TESTING, DOCUMENTATION, PRESENTATION).
"""

from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from core.agents.communication import AgentResponse


class TaskStage(str, Enum):
    RESEARCH = "RESEARCH"
    ARCHITECTURE = "ARCHITECTURE"
    IMPLEMENTATION = "IMPLEMENTATION"
    TESTING = "TESTING"
    DOCUMENTATION = "DOCUMENTATION"
    PRESENTATION = "PRESENTATION"


class SubTask(BaseModel):
    id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:8]}")
    title: str
    assigned_agent: str
    stage: TaskStage = TaskStage.IMPLEMENTATION
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending" # "pending" | "running" | "completed" | "failed" | "skipped"
    result: Optional[AgentResponse] = None
    input_context: Dict[str, Any] = Field(default_factory=dict)


class TaskDAG(BaseModel):
    dag_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_query: str
    subtasks: List[SubTask] = Field(default_factory=list)

    def get_subtask(self, subtask_id: str) -> Optional[SubTask]:
        for st in self.subtasks:
            if st.id == subtask_id:
                return st
        return None

    def get_ready_subtasks(self) -> List[SubTask]:
        """Returns pending subtasks whose dependencies have all completed successfully."""
        ready: List[SubTask] = []
        completed_ids = {st.id for st in self.subtasks if st.status == "completed"}

        for st in self.subtasks:
            if st.status == "pending":
                if all(dep_id in completed_ids for dep_id in st.dependencies):
                    ready.append(st)
        return ready

    def mark_completed(self, subtask_id: str, result: AgentResponse) -> None:
        st = self.get_subtask(subtask_id)
        if st:
            st.status = "completed"
            st.result = result

    def mark_failed(self, subtask_id: str, error: str) -> None:
        st = self.get_subtask(subtask_id)
        if st:
            st.status = "failed"
            st.result = AgentResponse.failed(error)

    def is_all_completed(self) -> bool:
        return all(st.status == "completed" for st in self.subtasks)

    def is_failed(self) -> bool:
        return any(st.status == "failed" for st in self.subtasks)


class TaskDecomposer:
    """Decomposes complex multi-agent goals into structured DAG pipelines."""

    @classmethod
    def decompose(cls, query: str) -> TaskDAG:
        dag = TaskDAG(original_query=query)
        q_lower = query.lower()

        # Complex multi-step detection
        has_research = any(w in q_lower for w in ["research", "investigate", "explore", "survey"])
        has_coding = any(w in q_lower for w in ["code", "build", "implement", "fix", "script", "app"])
        has_testing = any(w in q_lower for w in ["test", "verify", "run tests"])
        has_doc = any(w in q_lower for w in ["document", "readme", "write docs", "api doc"])
        has_presentation = any(w in q_lower for w in ["presentation", "deck", "slides", "pitch"])
        has_phone = any(w in q_lower for w in ["phone", "mobile", "android"])

        # Check if composite workflow
        indicators = sum([has_research, has_coding or has_testing, has_doc, has_presentation, has_phone])

        if indicators >= 2:
            prev_subtask_id: Optional[str] = None

            if has_research:
                st_res = SubTask(
                    title=f"Research topic: {query}",
                    assigned_agent="research_agent",
                    stage=TaskStage.RESEARCH,
                    dependencies=[],
                )
                dag.subtasks.append(st_res)
                prev_subtask_id = st_res.id

            if has_coding:
                st_code = SubTask(
                    title="Implement code solution",
                    assigned_agent="coding_agent",
                    stage=TaskStage.IMPLEMENTATION,
                    dependencies=[prev_subtask_id] if prev_subtask_id else [],
                )
                dag.subtasks.append(st_code)
                prev_subtask_id = st_code.id

            if has_testing:
                st_test = SubTask(
                    title="Run test suite and verify implementation",
                    assigned_agent="coding_agent",
                    stage=TaskStage.TESTING,
                    dependencies=[prev_subtask_id] if prev_subtask_id else [],
                )
                dag.subtasks.append(st_test)
                prev_subtask_id = st_test.id

            if has_doc:
                st_doc = SubTask(
                    title="Generate documentation and README",
                    assigned_agent="documentation_agent",
                    stage=TaskStage.DOCUMENTATION,
                    dependencies=[prev_subtask_id] if prev_subtask_id else [],
                )
                dag.subtasks.append(st_doc)
                prev_subtask_id = st_doc.id

            if has_presentation:
                st_pres = SubTask(
                    title="Generate presentation deck",
                    assigned_agent="presentation_agent",
                    stage=TaskStage.PRESENTATION,
                    dependencies=[prev_subtask_id] if prev_subtask_id else [],
                )
                dag.subtasks.append(st_pres)

            if has_phone:
                st_ph = SubTask(
                    title="Execute phone actions",
                    assigned_agent="phone_agent",
                    stage=TaskStage.IMPLEMENTATION,
                    dependencies=[prev_subtask_id] if prev_subtask_id else [],
                )
                dag.subtasks.append(st_ph)

            return dag

        # Single subtask default
        agent_name = "computer_agent"
        stage = TaskStage.IMPLEMENTATION
        if has_phone:
            agent_name = "phone_agent"
        elif has_presentation:
            agent_name = "presentation_agent"
            stage = TaskStage.PRESENTATION
        elif has_doc:
            agent_name = "documentation_agent"
            stage = TaskStage.DOCUMENTATION
        elif has_research:
            agent_name = "research_agent"
            stage = TaskStage.RESEARCH
        elif has_coding:
            agent_name = "coding_agent"
        elif any(w in q_lower for w in ["browser", "chrome", "youtube", "website"]):
            agent_name = "browser_agent"

        single = SubTask(
            title=query,
            assigned_agent=agent_name,
            stage=stage,
            dependencies=[],
        )
        dag.subtasks.append(single)
        return dag
