"""
SHIVANI Productivity Integrations Suite
"""

from integrations.base import BaseIntegration
from integrations.youtube.service import YouTubeService
from integrations.gmail.service import GmailService
from integrations.gmail.gmail_helper import GmailHelper
from integrations.linkedin.service import LinkedInService
from integrations.linkedin.linkedin_helper import LinkedInHelper
from integrations.github.service import GitHubService
from integrations.research.service import ResearchService

__all__ = [
    "BaseIntegration",
    "YouTubeService",
    "GmailService",
    "GmailHelper",
    "LinkedInService",
    "LinkedInHelper",
    "GitHubService",
    "ResearchService",
]
