"""
SHIVANI Content Generation Agent
Produces professional social posts, email drafts, documentation, README files,
summaries, and presentation outlines.
Enforces strict separation of DRAFT and PUBLISHED states.
"""

from typing import Any, Dict, List, Optional
from core.projects.models import ProjectMetadata


class ContentAgent:
    """Autonomous agent specialized in synthesizing structured, high-impact content."""

    def generate_linkedin_post(
        self,
        project: ProjectMetadata,
        tone: str = "professional",
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes a compelling LinkedIn project showcase post from local project metadata.
        Output is strictly a DRAFT.
        """
        title = project.name.replace("-", " ").replace("_", " ")
        if title.islower():
            title = title.title()
        tech_str = ", ".join(project.frameworks or project.languages or ["Python"])
        
        hook = f"🚀 Excited to share what I've been building: **{title}**!"
        summary = project.readme_summary or f"An intelligent project built using {tech_str}."

        features_bullets = ""
        if project.key_features:
            features_bullets = "\nKey Highlights:\n" + "\n".join(f"✨ {feat}" for feat in project.key_features[:4])

        links_block = ""
        if project.git_remote:
            links_block += f"\n\n🔗 GitHub: {project.git_remote}"
        if project.demo_url:
            links_block += f"\n🌐 Live Demo: {project.demo_url}"

        tags = "\n\n#SoftwareEngineering #ArtificialIntelligence #Python #TechInnovation #BuildInPublic #OpenSource"
        
        full_text = f"{hook}\n\n{summary}{features_bullets}{links_block}\n\nFeedback and thoughts are welcome! 👇{tags}"
        
        if custom_instructions:
            full_text += f"\n\n[Note: {custom_instructions}]"

        return {
            "status": "DRAFT",
            "project_name": project.name,
            "tone": tone,
            "content": full_text,
            "character_count": len(full_text),
            "requires_confirmation": True
        }

    def generate_email_draft(
        self,
        recipient: str,
        subject: str,
        key_points: List[str],
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """Drafts an email based on bullet points. Strictly returns DRAFT status."""
        bullets = "\n".join(f"- {p}" for p in key_points)
        body = f"""Hi {recipient},

I hope this message finds you well.

{bullets}

Please let me know your thoughts or if you have any questions.

Best regards,
SHIVANI User"""
        return {
            "status": "DRAFT",
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "requires_confirmation": True
        }

    def generate_comment(self, post_content: str, perspective: str = "insightful") -> Dict[str, Any]:
        """Drafts an insightful response comment to a LinkedIn or forum post."""
        snippet = post_content[:150].strip()
        comment = f"Great insights regarding '{snippet}...'! The emphasis on modular design and automated verification makes a noticeable difference in long-term reliability. Thanks for sharing!"
        return {
            "status": "DRAFT",
            "comment": comment,
            "requires_confirmation": True
        }

    def generate_readme(
        self,
        project_name: str,
        description: str,
        tech_stack: List[str],
        features: List[str],
        run_command: str = "python main.py"
    ) -> str:
        """Generates comprehensive README.md content."""
        stack_str = ", ".join(tech_stack)
        feat_str = "\n".join(f"- {f}" for f in features)
        return f"""# {project_name}

{description}

## Tech Stack
{stack_str}

## Key Features
{feat_str}

## Quick Start
```bash
# Clone repository
git clone <repo-url>
cd {project_name.lower()}

# Run application
{run_command}
```
"""

    def generate_presentation_outline(self, topic: str, slide_count: int = 5) -> List[Dict[str, Any]]:
        """Generates structured presentation slides outline."""
        slides = [
            {"slide": 1, "title": f"Introduction to {topic}", "points": ["Overview", "Motivation", "Current Landscape"]},
            {"slide": 2, "title": "Problem Statement & Challenges", "points": ["Bottlenecks", "Safety constraints", "User impact"]},
            {"slide": 3, "title": "Proposed Architecture & Solution", "points": ["System design", "Key components", "Integration flows"]},
            {"slide": 4, "title": "Verification & Results", "points": ["Performance benchmarks", "Safety metrics", "Real-world test outcomes"]},
            {"slide": 5, "title": "Conclusion & Future Roadmap", "points": ["Summary", "Next phases", "Q&A"]},
        ]
        return slides[:slide_count]
