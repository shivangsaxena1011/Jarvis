"""
SHIVANI Hierarchical Task Decomposer.
Decomposes complex Goals into interconnected SubTaskPlans with typed input/output data pipelines.
"""

from typing import List, Optional, Dict, Any
from planning.models import Goal, SubTaskPlan
from security.permissions.engine import RiskLevel


class HierarchicalTaskDecomposer:
    """Decomposes goals into specialized subtasks with inputs, outputs, and dependencies."""

    def decompose(self, goal: Goal) -> List[SubTaskPlan]:
        """Translates a structured Goal into ordered SubTaskPlans with dependencies."""
        q_lower = goal.objective.lower()
        subtasks: List[SubTaskPlan] = []

        # Check for multi-stage composite workflow
        has_research = "research_findings" in goal.desired_outputs or any(w in q_lower for w in ["research", "investigate", "compare", "survey"])
        has_report = "report" in goal.desired_outputs or any(w in q_lower for w in ["report", "document", "readme", "write-up"])
        has_presentation = "presentation" in goal.desired_outputs or any(w in q_lower for w in ["presentation", "slides", "deck", "pitch"])
        has_social = "social_post" in goal.desired_outputs or any(w in q_lower for w in ["linkedin", "post", "social", "tweet"])
        has_coding = "code" in goal.desired_outputs or any(w in q_lower for w in ["code", "fix", "implement", "build", "bug", "feature"])
        has_testing = "test_results" in goal.desired_outputs or any(w in q_lower for w in ["test", "verify", "run tests"])
        has_phone = any(w in q_lower for w in ["phone", "mobile", "android"])

        # Composite Content/Productivity Workflow: Research -> Report -> Presentation -> LinkedIn
        if sum([has_research, has_report, has_presentation, has_social]) >= 2:
            prev_id: Optional[str] = None

            if has_research:
                st_res = SubTaskPlan(
                    title=f"Research and synthesize: {goal.objective}",
                    description="Discover authoritative sources, extract insights, and synthesize comparison findings.",
                    assigned_agent="research_agent",
                    stage="RESEARCH",
                    outputs=["research_findings"],
                    risk_level=RiskLevel.SAFE,
                    expected_result="Synthesized research findings markdown.",
                    verification_method="validate_research_summary",
                )
                subtasks.append(st_res)
                prev_id = st_res.id

            if has_report:
                deps = [prev_id] if prev_id else []
                st_rep = SubTaskPlan(
                    title="Generate comprehensive structured report",
                    description="Structure, draft, and format the comprehensive report document based on research findings.",
                    assigned_agent="documentation_agent",
                    stage="DOCUMENTATION",
                    inputs={"research_context": prev_id} if prev_id else {},
                    outputs=["report_markdown"],
                    dependencies=deps,
                    risk_level=RiskLevel.LOW_RISK,
                    expected_result="Structured report document saved to workspace.",
                    verification_method="validate_file_exists",
                )
                subtasks.append(st_rep)
                prev_id = st_rep.id

            if has_presentation:
                deps = [prev_id] if prev_id else []
                st_pres = SubTaskPlan(
                    title="Build executive pitch presentation deck",
                    description="Generate slide structure, key takeaways, and compile python-pptx presentation deck.",
                    assigned_agent="presentation_agent",
                    stage="PRESENTATION",
                    inputs={"source_document": prev_id} if prev_id else {},
                    outputs=["presentation_pptx"],
                    dependencies=deps,
                    risk_level=RiskLevel.LOW_RISK,
                    expected_result="Presentation PowerPoint (.pptx) file rendered in workspace.",
                    verification_method="validate_presentation_slides",
                )
                subtasks.append(st_pres)

            if has_social:
                # Can depend on report or research
                deps = [prev_id] if prev_id else []
                st_soc = SubTaskPlan(
                    title="Draft LinkedIn post for executive review",
                    description="Compose an engaging, professional summary post ready for user approval before publishing.",
                    assigned_agent="browser_agent",
                    stage="DISTRIBUTION",
                    inputs={"content_source": prev_id} if prev_id else {},
                    outputs=["social_draft_text"],
                    dependencies=deps,
                    risk_level=RiskLevel.SENSITIVE,
                    expected_result="Social media draft presented for human approval.",
                    verification_method="require_user_confirmation",
                )
                subtasks.append(st_soc)

            return subtasks

        # Composite Coding Workflow: Inspect -> Implement -> Test
        if has_coding and (has_testing or "fix" in q_lower or "bug" in q_lower or "build" in q_lower):
            st_analyze = SubTaskPlan(
                title=f"Analyze codebase and diagnose issue: {goal.objective}",
                description="Inspect repository AST, find relevant files, and locate root cause.",
                assigned_agent="coding_agent",
                stage="ANALYSIS",
                outputs=["diagnostic_plan"],
                risk_level=RiskLevel.SAFE,
                expected_result="Identification of target files and patch strategy.",
            )
            subtasks.append(st_analyze)

            st_patch = SubTaskPlan(
                title="Implement code modifications and patch files",
                description="Apply code edits using safe file replacement tools.",
                assigned_agent="coding_agent",
                stage="IMPLEMENTATION",
                inputs={"plan": st_analyze.id},
                dependencies=[st_analyze.id],
                outputs=["modified_files"],
                risk_level=RiskLevel.LOW_RISK,
                expected_result="Code files updated cleanly without syntax errors.",
            )
            subtasks.append(st_patch)

            if has_testing or "test" in q_lower:
                st_test = SubTaskPlan(
                    title="Execute test suite and verify patch",
                    description="Run project tests to verify the fix and prevent regressions.",
                    assigned_agent="coding_agent",
                    stage="TESTING",
                    inputs={"patched_code": st_patch.id},
                    dependencies=[st_patch.id],
                    outputs=["test_results"],
                    risk_level=RiskLevel.LOW_RISK,
                    expected_result="All test assertions pass with zero regressions.",
                )
                subtasks.append(st_test)

            return subtasks

        # Mobile Phone Agent Workflow
        if has_phone:
            subtasks.append(
                SubTaskPlan(
                    title=f"Execute Android device action: {goal.objective}",
                    description="Route command to paired mobile companion device over secure device bridge.",
                    assigned_agent="phone_agent",
                    stage="MOBILE_EXECUTION",
                    outputs=["mobile_action_result"],
                    risk_level=RiskLevel.LOW_RISK if "delete" not in q_lower else RiskLevel.SENSITIVE,
                    expected_result="Mobile action completed and verified via UI accessibility dump.",
                )
            )
            return subtasks

        # Default / Single focused task
        # Determine best agent
        assigned_agent = "computer_agent"
        if any(w in q_lower for w in ["search web", "browse", "website", "chrome", "google"]):
            assigned_agent = "browser_agent"
        elif any(w in q_lower for w in ["git", "python", "code", "file", "function"]):
            assigned_agent = "coding_agent"

        subtasks.append(
            SubTaskPlan(
                title=goal.objective,
                description=f"Directly execute task: {goal.objective}",
                assigned_agent=assigned_agent,
                stage="EXECUTION",
                outputs=["execution_result"],
                risk_level=RiskLevel.SAFE,
                expected_result="Requested action successfully executed and visually verified.",
            )
        )
        return subtasks
