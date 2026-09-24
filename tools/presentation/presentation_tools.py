"""
SHIVANI Presentation Registered Tools
Registered tools for generating PowerPoint (.pptx) decks, pitch scripts,
judge Q&A bundles, and slide layout inspection.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from agents.presentation.agent import PresentationAgent
from agents.presentation.models import PresentationMode


class PresentationGenerateDeckArgs(BaseModel):
    title: str = Field(description="Presentation title")
    project_name: str = Field(description="Name of project or product")
    problem_statement: str = Field(description="Core problem description")
    solution_summary: str = Field(description="Summary of proposed solution")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies used")
    key_features: List[str] = Field(default_factory=list, description="Key features or highlights")
    mode: str = Field(default="hackathon", description="Presentation mode: 'hackathon', 'technical', 'executive'")
    target_duration: int = Field(default=5, description="Target presentation duration in minutes")


class PresentationGenerateDeckTool(BaseTool):
    name = "presentation.generate_deck"
    description = "Generate a production-quality PowerPoint (.pptx) presentation deck with speaker notes."
    permission_level = RiskLevel.SAFE
    args_schema = PresentationGenerateDeckArgs
    timeout = 35.0

    def __init__(self, presentation_agent: Optional[PresentationAgent] = None):
        super().__init__()
        self.agent = presentation_agent or PresentationAgent()

    async def run(
        self,
        title: str,
        project_name: str,
        problem_statement: str,
        solution_summary: str,
        tech_stack: Optional[List[str]] = None,
        key_features: Optional[List[str]] = None,
        mode: str = "hackathon",
        target_duration: int = 5
    ) -> Dict[str, Any]:
        pm = PresentationMode(mode) if mode in PresentationMode._value2member_map_ else PresentationMode.HACKATHON
        deck = self.agent.build_deck(
            title=title,
            project_name=project_name,
            problem_statement=problem_statement,
            solution_summary=solution_summary,
            tech_stack=tech_stack or [],
            key_features=key_features or [],
            mode=pm,
            target_duration=target_duration
        )
        return deck.model_dump()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        pptx_path = result_data.get("pptx_path")
        return {"verified": bool(pptx_path) and result_data.get("total_slides", 0) > 0}


class PresentationGeneratePitchArgs(BaseModel):
    project_name: str = Field(description="Project name")
    problem: str = Field(description="Problem statement")
    solution: str = Field(description="Solution summary")
    features: List[str] = Field(default_factory=list, description="Key features")


class PresentationGeneratePitchTool(BaseTool):
    name = "presentation.generate_pitch"
    description = "Generate multi-duration pitch scripts (30-second, 1-minute, 3-minute, 5-minute)."
    permission_level = RiskLevel.SAFE
    args_schema = PresentationGeneratePitchArgs
    timeout = 15.0

    def __init__(self, presentation_agent: Optional[PresentationAgent] = None):
        super().__init__()
        self.agent = presentation_agent or PresentationAgent()

    async def run(self, project_name: str, problem: str, solution: str, features: Optional[List[str]] = None) -> Dict[str, Any]:
        pitches = self.agent.generate_pitches(project_name, problem, solution, features or [])
        return pitches.model_dump()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("pitch_1m")) and bool(result_data.get("pitch_3m"))}


class PresentationGenerateQAArgs(BaseModel):
    project_name: str = Field(description="Project name")
    tech_stack: List[str] = Field(default_factory=list, description="Tech stack")
    solution: str = Field(description="Solution summary")


class PresentationGenerateQATool(BaseTool):
    name = "presentation.generate_qa"
    description = "Generate anticipated judge Q&A across 8 dimensions (Technical, Security, Scalability, AI/ML, Business, etc.)."
    permission_level = RiskLevel.SAFE
    args_schema = PresentationGenerateQAArgs
    timeout = 15.0

    def __init__(self, presentation_agent: Optional[PresentationAgent] = None):
        super().__init__()
        self.agent = presentation_agent or PresentationAgent()

    async def run(self, project_name: str, tech_stack: Optional[List[str]] = None, solution: str = "") -> Dict[str, Any]:
        qa_list = self.agent.generate_qa(project_name, tech_stack or [], solution)
        return {"count": len(qa_list), "qa_items": [q.model_dump() for q in qa_list]}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("count", 0) > 0}
