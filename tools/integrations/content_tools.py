"""
SHIVANI Content Generation Registered Tools
Enforces draft status, structured output, and safety for generated materials.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from agents.content.agent import ContentAgent
from core.projects.models import ProjectMetadata


class GenerateLinkedInPostArgs(BaseModel):
    project_name: Optional[str] = Field(default=None, description="Name of the project")
    project_path: Optional[str] = Field(default=None, description="Path of the project")
    readme_summary: Optional[str] = Field(default=None, description="Summary or description")
    frameworks: Optional[List[str]] = Field(default_factory=list, description="Frameworks or tech stack used")
    git_remote: Optional[str] = Field(default=None, description="Git remote repository URL")
    demo_url: Optional[str] = Field(default=None, description="Live demo URL")
    tone: str = Field(default="professional", description="Tone of post: professional, casual, technical")
    custom_instructions: Optional[str] = Field(default=None, description="Additional custom instructions")


class ContentGenerateLinkedInPostTool(BaseTool):
    name = "content.generate_linkedin_post"
    description = "Generate a compelling LinkedIn showcase post draft from project metadata."
    permission_level = RiskLevel.SAFE
    args_schema = GenerateLinkedInPostArgs
    timeout = 15.0

    def __init__(self, agent: Optional[ContentAgent] = None):
        super().__init__()
        self.agent = agent or ContentAgent()

    async def run(
        self,
        project_name: Optional[str] = None,
        project_path: Optional[str] = None,
        readme_summary: Optional[str] = None,
        frameworks: Optional[List[str]] = None,
        git_remote: Optional[str] = None,
        demo_url: Optional[str] = None,
        tone: str = "professional",
        custom_instructions: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        # Handle dict or ProjectMetadata
        p_name = project_name or kwargs.get("name") or "My Project"
        meta = ProjectMetadata(
            name=p_name,
            path=project_path or "",
            readme_summary=readme_summary or kwargs.get("description", ""),
            frameworks=frameworks or [],
            git_remote=git_remote,
            demo_url=demo_url
        )
        return self.agent.generate_linkedin_post(meta, tone=tone, custom_instructions=custom_instructions)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "verified": result_data.get("status") == "DRAFT" and bool(result_data.get("content")),
            "status": result_data.get("status"),
            "character_count": result_data.get("character_count", 0)
        }


class GenerateEmailArgs(BaseModel):
    recipient: str = Field(description="Email recipient name or address")
    subject: str = Field(description="Subject line")
    key_points: List[str] = Field(description="Key bullet points to convey in the email")
    tone: str = Field(default="professional", description="Email tone")


class ContentGenerateEmailTool(BaseTool):
    name = "content.generate_email"
    description = "Draft a professional email from key bullet points (strictly DRAFT status)."
    permission_level = RiskLevel.SAFE
    args_schema = GenerateEmailArgs
    timeout = 15.0

    def __init__(self, agent: Optional[ContentAgent] = None):
        super().__init__()
        self.agent = agent or ContentAgent()

    async def run(
        self,
        recipient: str,
        subject: str,
        key_points: List[str],
        tone: str = "professional"
    ) -> Dict[str, Any]:
        return self.agent.generate_email_draft(recipient, subject, key_points, tone)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "verified": result_data.get("status") == "DRAFT" and bool(result_data.get("body")),
            "status": result_data.get("status")
        }


class GenerateCommentArgs(BaseModel):
    post_content: str = Field(description="Content of the post being commented on")
    perspective: str = Field(default="insightful", description="Tone/perspective of comment")


class ContentGenerateCommentTool(BaseTool):
    name = "content.generate_comment"
    description = "Draft an insightful comment response for a social or forum post."
    permission_level = RiskLevel.SAFE
    args_schema = GenerateCommentArgs
    timeout = 10.0

    def __init__(self, agent: Optional[ContentAgent] = None):
        super().__init__()
        self.agent = agent or ContentAgent()

    async def run(self, post_content: str, perspective: str = "insightful") -> Dict[str, Any]:
        return self.agent.generate_comment(post_content, perspective)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "verified": result_data.get("status") == "DRAFT" and bool(result_data.get("comment")),
            "status": result_data.get("status")
        }


class GenerateReadmeArgs(BaseModel):
    project_name: str = Field(description="Project name")
    description: str = Field(description="Brief project description")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies / languages used")
    features: List[str] = Field(default_factory=list, description="Key features")
    run_command: str = Field(default="python main.py", description="Quick start command")


class ContentGenerateReadmeTool(BaseTool):
    name = "content.generate_readme"
    description = "Generate markdown content for a project README.md."
    permission_level = RiskLevel.SAFE
    args_schema = GenerateReadmeArgs
    timeout = 15.0

    def __init__(self, agent: Optional[ContentAgent] = None):
        super().__init__()
        self.agent = agent or ContentAgent()

    async def run(
        self,
        project_name: str,
        description: str,
        tech_stack: Optional[List[str]] = None,
        features: Optional[List[str]] = None,
        run_command: str = "python main.py"
    ) -> Dict[str, Any]:
        content = self.agent.generate_readme(
            project_name=project_name,
            description=description,
            tech_stack=tech_stack or ["Python"],
            features=features or [],
            run_command=run_command
        )
        return {"status": "success", "content": content, "length": len(content)}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("content")), "length": result_data.get("length", 0)}


class GeneratePresentationArgs(BaseModel):
    topic: str = Field(description="Presentation topic")
    slide_count: int = Field(default=5, description="Number of slides")


class ContentGeneratePresentationTool(BaseTool):
    name = "content.generate_presentation"
    description = "Generate a structured outline for presentation slides."
    permission_level = RiskLevel.SAFE
    args_schema = GeneratePresentationArgs
    timeout = 15.0

    def __init__(self, agent: Optional[ContentAgent] = None):
        super().__init__()
        self.agent = agent or ContentAgent()

    async def run(self, topic: str, slide_count: int = 5) -> Dict[str, Any]:
        slides = self.agent.generate_presentation_outline(topic, slide_count)
        return {"topic": topic, "slide_count": len(slides), "slides": slides}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": len(result_data.get("slides", [])) > 0, "slide_count": result_data.get("slide_count", 0)}
