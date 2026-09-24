"""
SHIVANI Integration Tools
Exports all Phase 5 cross-application registered tools.
"""

from tools.integrations.youtube_tools import (
    YouTubeSearchTool,
    YouTubeOpenVideoTool,
    YouTubePlayTool,
    YouTubePauseTool,
    YouTubeStopTool,
    YouTubeGetCurrentVideoTool,
)
from tools.integrations.gmail_tools import (
    GmailOpenTool,
    GmailListUnreadTool,
    GmailSearchTool,
    GmailSummarizeTool,
    GmailCleanupProposalTool,
    GmailExecuteCleanupTool,
    GmailDeleteTool,
)
from tools.integrations.linkedin_tools import (
    LinkedInOpenTool,
    LinkedInReadFeedTool,
    LinkedInPreparePostTool,
    LinkedInPrepareCommentTool,
    LinkedInPublishPostTool,
)
from tools.integrations.github_tools import (
    GitHubInspectRepositoryTool,
    GitHubReadFileTool,
    GitHubListFilesTool,
    GitHubReadIssuesTool,
    GitHubCreateIssueTool,
    GitHubInspectRunnableTool,
)
from tools.integrations.research_tools import (
    ResearchSearchTool,
    ResearchOpenSourceTool,
    ResearchSummarizeTool,
    ResearchSaveReportTool,
)
from tools.integrations.project_tools import (
    ProjectFindTool,
    ProjectListTool,
)
from tools.integrations.content_tools import (
    ContentGenerateLinkedInPostTool,
    ContentGenerateEmailTool,
    ContentGenerateCommentTool,
    ContentGenerateReadmeTool,
    ContentGeneratePresentationTool,
)

__all__ = [
    # YouTube
    "YouTubeSearchTool",
    "YouTubeOpenVideoTool",
    "YouTubePlayTool",
    "YouTubePauseTool",
    "YouTubeStopTool",
    "YouTubeGetCurrentVideoTool",
    # Gmail
    "GmailOpenTool",
    "GmailListUnreadTool",
    "GmailSearchTool",
    "GmailSummarizeTool",
    "GmailCleanupProposalTool",
    "GmailExecuteCleanupTool",
    "GmailDeleteTool",
    # LinkedIn
    "LinkedInOpenTool",
    "LinkedInReadFeedTool",
    "LinkedInPreparePostTool",
    "LinkedInPrepareCommentTool",
    "LinkedInPublishPostTool",
    # GitHub
    "GitHubInspectRepositoryTool",
    "GitHubReadFileTool",
    "GitHubListFilesTool",
    "GitHubReadIssuesTool",
    "GitHubCreateIssueTool",
    "GitHubInspectRunnableTool",
    # Research
    "ResearchSearchTool",
    "ResearchOpenSourceTool",
    "ResearchSummarizeTool",
    "ResearchSaveReportTool",
    # Project
    "ProjectFindTool",
    "ProjectListTool",
    # Content
    "ContentGenerateLinkedInPostTool",
    "ContentGenerateEmailTool",
    "ContentGenerateCommentTool",
    "ContentGenerateReadmeTool",
    "ContentGeneratePresentationTool",
]
