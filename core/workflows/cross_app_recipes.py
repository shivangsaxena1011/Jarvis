"""
SHIVANI Cross-Application Workflow Recipes
Pre-configured multi-step recipes orchestrating projects, files, browsers, social media, and research.
"""

from typing import Optional
from core.workflows.models import Workflow, WorkflowStep
from security.permissions.engine import RiskLevel


class CrossAppRecipes:
    """Factory for standard cross-application workflows."""

    @staticmethod
    def project_to_linkedin(project_name_or_query: str, image_path: Optional[str] = None) -> Workflow:
        """
        Recipe 1: Project to LinkedIn Showcase Post
        1. Find and inspect local project
        2. Generate professional showcase post draft
        3. Prepare LinkedIn draft
        4. (Approval Gate) Publish post to LinkedIn
        """
        steps = [
            WorkflowStep(
                id="step_find_project",
                description=f"Locate and inspect local project '{project_name_or_query}'",
                agent="system",
                tool="project.find",
                input={"query": project_name_or_query},
                expected_output="ProjectMetadata loaded",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_gen_content",
                description="Synthesize professional LinkedIn post draft from project metadata",
                agent="content",
                tool="content.generate_linkedin_post",
                input={"project_name": project_name_or_query},
                expected_output="LinkedIn draft text generated",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_prepare_post",
                description="Prepare LinkedIn post in DRAFT mode",
                agent="linkedin",
                tool="linkedin.prepare_post",
                input={"post_text": "{content}", "image_path": image_path or ""},
                expected_output="Draft created with unique ID",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_publish_post",
                description="Publish post to LinkedIn feed (Requires Explicit User Confirmation)",
                agent="linkedin",
                tool="linkedin.publish_post",
                input={"draft_id": "{draft_id}"},
                expected_output="Post published and verified",
                permission=RiskLevel.CRITICAL,
                requires_approval=True
            ),
        ]
        return Workflow(
            name="Project to LinkedIn Showcase",
            description=f"Creates and publishes LinkedIn showcase for '{project_name_or_query}' with mandatory approval.",
            steps=steps
        )

    @staticmethod
    def gmail_summary() -> Workflow:
        """
        Recipe 2: Gmail Daily Inbox Summary
        1. Inspect Gmail inbox
        2. Categorize and generate executive summary
        """
        steps = [
            WorkflowStep(
                id="step_list_unread",
                description="Inspect Gmail inbox and retrieve unread email messages",
                agent="gmail",
                tool="gmail.list_unread",
                input={"limit": 25},
                expected_output="List of unread emails",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_summarize_inbox",
                description="Categorize messages and generate executive summary",
                agent="gmail",
                tool="gmail.summarize",
                input={},
                expected_output="Categorized summary of inbox",
                permission=RiskLevel.SAFE
            ),
        ]
        return Workflow(
            name="Gmail Daily Summary",
            description="Categorizes and summarizes recent unread Gmail messages.",
            steps=steps
        )

    @staticmethod
    def gmail_cleanup() -> Workflow:
        """
        Recipe 3: Gmail Two-Stage Inbox Cleanup
        1. Scan unread emails
        2. Classify promotional/newsletters and generate cleanup proposal
        3. (Approval Gate) Execute batch archive
        """
        steps = [
            WorkflowStep(
                id="step_scan_emails",
                description="Scan inbox and generate executive summary",
                agent="gmail",
                tool="gmail.summarize",
                input={},
                expected_output="Categorized summary of inbox",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_cleanup_proposal",
                description="Analyze emails and formulate cleanup proposal",
                agent="gmail",
                tool="gmail.cleanup_proposal",
                input={},
                expected_output="Structured proposal with categorized counts",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_execute_cleanup",
                description="Archive promotional and newsletter emails (Requires User Confirmation)",
                agent="gmail",
                tool="gmail.execute_cleanup",
                input={"proposal_id": "{proposal_id}", "action": "archive"},
                expected_output="Batch archive completed and verified",
                permission=RiskLevel.SENSITIVE,
                requires_approval=True
            ),
        ]
        return Workflow(
            name="Gmail Inbox Cleanup",
            description="Scans, proposes, and safely archives promotional emails with user authorization.",
            steps=steps
        )

    @staticmethod
    def research_report(topic: str) -> Workflow:
        """
        Recipe 4: Web & Literature Research Report
        1. Query web & literature sources
        2. Synthesize findings
        3. Save structured bundle (report.md, sources.json, summary.json)
        """
        steps = [
            WorkflowStep(
                id="step_search_sources",
                description=f"Query search engines and academic sources for '{topic}'",
                agent="research",
                tool="research.search",
                input={"query": topic, "limit": 5},
                expected_output="Ranked citations and snippets",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_summarize_research",
                description="Synthesize key findings and comparative insights",
                agent="research",
                tool="research.summarize",
                input={"query": topic},
                expected_output="Synthesized research summary",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_save_bundle",
                description="Save research bundle (report.md, sources.json, summary.json)",
                agent="research",
                tool="research.save",
                input={"query": topic},
                expected_output="Research files written to disk",
                permission=RiskLevel.SAFE
            ),
        ]
        return Workflow(
            name="Web & Literature Research Report",
            description=f"Conducts deep research on '{topic}' and creates a cited report.",
            steps=steps
        )

    @staticmethod
    def github_inspect_and_run(repo_name_or_query: str) -> Workflow:
        """
        Recipe 5: GitHub Project Inspection & Safe Run
        1. Inspect repository and package files
        2. Determine safe startup command
        3. (Approval Gate if risky) Run service
        """
        steps = [
            WorkflowStep(
                id="step_inspect_repo",
                description=f"Inspect repository structure and configuration for '{repo_name_or_query}'",
                agent="github",
                tool="github.inspect_repository",
                input={"repo_path_or_name": repo_name_or_query},
                expected_output="Repository metadata and entrypoints",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_inspect_runnable",
                description="Analyze package files and verify safe startup command",
                agent="github",
                tool="github.inspect_runnable",
                input={"repo_path": "{path}"},
                expected_output="Safe startup command verified",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_run_service",
                description="Execute application service (Requires Confirmation if Potentially Risky)",
                agent="system",
                tool="terminal.execute",
                input={"command": "{command}"},
                expected_output="Service started",
                permission=RiskLevel.SENSITIVE,
                requires_approval=True
            ),
        ]
        return Workflow(
            name="GitHub Project Inspection & Run",
            description=f"Inspects '{repo_name_or_query}' and safely launches local service.",
            steps=steps
        )

    @staticmethod
    def phone_photo_to_linkedin(topic: str, photo_query: str = "hackathon") -> Workflow:
        """
        Recipe 6: Phone Photo to LinkedIn Showcase Flow
        1. Search phone photos matching query (e.g. 'hackathon')
        2. Transfer selected photo securely to local laptop workspace
        3. Synthesize LinkedIn post draft highlighting photo & topic
        4. Prepare LinkedIn draft
        5. (Approval Gate) Publish post with photo preview
        """
        steps = [
            WorkflowStep(
                id="step_phone_find_photo",
                description=f"Search user photos on Android phone matching '{photo_query}'",
                agent="phone",
                tool="android.list_photos",
                input={"query": photo_query, "limit": 5},
                expected_output="Matching photo candidates loaded",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_phone_transfer_photo",
                description="Transfer selected photo to laptop workspace for publication",
                agent="phone",
                tool="android.transfer_file",
                input={"photo_id": "photo-101"},
                expected_output="Local file path for transferred photo",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_gen_content",
                description=f"Generate professional LinkedIn post draft for '{topic}'",
                agent="content",
                tool="content.generate_linkedin_post",
                input={"project_name": topic},
                expected_output="LinkedIn draft text generated",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_prepare_post",
                description="Prepare LinkedIn post in DRAFT mode with transferred photo",
                agent="linkedin",
                tool="linkedin.prepare_post",
                input={"post_text": "{content}", "image_path": "{local_path}"},
                expected_output="Draft created with unique ID",
                permission=RiskLevel.SAFE
            ),
            WorkflowStep(
                id="step_publish_post",
                description="Publish post to LinkedIn feed (Requires Explicit User Approval)",
                agent="linkedin",
                tool="linkedin.publish_post",
                input={"draft_id": "{draft_id}"},
                expected_output="Post published and verified",
                permission=RiskLevel.CRITICAL,
                requires_approval=True
            ),
        ]
        return Workflow(
            name="Phone Photo to LinkedIn",
            description=f"Cross-device pipeline: Find photo on phone for '{topic}', transfer to laptop, and draft LinkedIn post.",
            steps=steps
        )


# Convenience function aliases
def create_project_to_linkedin_workflow(project_name: str, image_path: Optional[str] = None) -> Workflow:
    return CrossAppRecipes.project_to_linkedin(project_name, image_path)


def create_gmail_summary_workflow() -> Workflow:
    return CrossAppRecipes.gmail_summary()


def create_gmail_triage_workflow(max_age_days: int = 30) -> Workflow:
    return CrossAppRecipes.gmail_cleanup()


def create_research_workflow(topic: str = "AI Agents", output_dir: Optional[str] = None) -> Workflow:
    wf = CrossAppRecipes.research_report(topic)
    if output_dir:
        for s in wf.steps:
            if s.tool == "research.save":
                s.input["output_dir"] = output_dir
    return wf


def create_github_inspect_and_run_workflow(repo_name_or_query: str) -> Workflow:
    return CrossAppRecipes.github_inspect_and_run(repo_name_or_query)


def create_hackathon_project_workflow(
    project_name: str,
    project_path: str,
    problem_statement: str
) -> Workflow:
    """
    Recipe 5: Unified Professional Hackathon Master Workflow
    Chains Research -> Architecture -> Implementation Inspection -> Testing -> Documentation -> Presentation
    with stage checkpointing.
    """
    steps = [
        WorkflowStep(
            id="step_research",
            stage="research",
            description=f"Conduct multi-source research on {problem_statement}",
            agent="research",
            tool="research.search",
            input={"query": problem_statement, "limit": 4},
            expected_output="Gathered authoritative sources",
            permission=RiskLevel.SAFE
        ),
        WorkflowStep(
            id="step_architecture",
            stage="architecture",
            description=f"Synthesize architecture document for {project_name}",
            agent="documentation",
            tool="documentation.generate_architecture_doc",
            input={"project_path": project_path},
            expected_output="Architecture decision record",
            permission=RiskLevel.SAFE
        ),
        WorkflowStep(
            id="step_inspect_impl",
            stage="implementation",
            description=f"Inspect implementation and detect stack for {project_name}",
            agent="coding",
            tool="coding.inspect_project",
            input={"project_path": project_path},
            expected_output="Stack specifications",
            permission=RiskLevel.SAFE
        ),
        WorkflowStep(
            id="step_run_tests",
            stage="testing",
            description=f"Execute automated test suite for {project_name}",
            agent="coding",
            tool="coding.run_tests",
            input={"project_path": project_path},
            expected_output="Test execution report",
            permission=RiskLevel.SAFE
        ),
        WorkflowStep(
            id="step_documentation",
            stage="documentation",
            description=f"Generate production README.md for {project_name}",
            agent="documentation",
            tool="documentation.generate_readme",
            input={"project_path": project_path},
            expected_output="Generated README",
            permission=RiskLevel.SAFE
        ),
        WorkflowStep(
            id="step_presentation",
            stage="presentation",
            description=f"Build PowerPoint pitch deck for {project_name}",
            agent="presentation",
            tool="presentation.generate_deck",
            input={
                "title": f"{project_name} Pitch Deck",
                "project_name": project_name,
                "problem_statement": problem_statement,
                "solution_summary": f"Autonomous AI-powered solution for {problem_statement}",
                "tech_stack": ["Python", "FastAPI", "AI/ML"],
                "key_features": ["100% verified execution", "Stage checkpointing", "Cross-agent workflows"]
            },
            expected_output="Generated presentation artifact (.pptx)",
            permission=RiskLevel.SAFE
        )
    ]
    return Workflow(
        name=f"Hackathon: {project_name}",
        description=f"End-to-end hackathon pipeline for {project_name}: research, architecture, implementation, test, documentation, and deck.",
        steps=steps
    )


def create_phone_photo_to_linkedin_workflow(topic: str, photo_query: str = "hackathon") -> Workflow:
    """Helper factory for Recipe 6."""
    return CrossAppRecipes.phone_photo_to_linkedin(topic=topic, photo_query=photo_query)


