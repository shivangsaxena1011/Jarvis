"""
SHIVANI Browser Tool Suite
Complete registered tools for universal autonomous browser operations.
"""

from tools.browser.navigation_tools import (
    BrowserOpenTool,
    BrowserCloseTool,
    BrowserNavigateTool,
    BrowserBackTool,
    BrowserForwardTool,
    BrowserRefreshTool,
    BrowserGetTitleTool,
    BrowserGetUrlTool,
    BrowserSearchTool,
)
from tools.browser.interaction_tools import (
    BrowserFindTool,
    BrowserClickTool,
    BrowserDoubleClickTool,
    BrowserTypeTool,
    BrowserClearTool,
    BrowserSelectTool,
    BrowserPressKeyTool,
    BrowserScrollTool,
    BrowserScrollToTool,
)
from tools.browser.tab_tools import (
    BrowserNewTabTool,
    BrowserSwitchTabTool,
    BrowserCloseTabTool,
    BrowserListTabsTool,
)
from tools.browser.content_tools import (
    BrowserExtractTextTool,
    BrowserExtractLinksTool,
    BrowserSummarizeTool,
    BrowserExtractDataTool,
    BrowserScreenshotTool,
    BrowserUploadFileTool,
    BrowserDownloadFileTool,
    BrowserPlayYouTubeTool,
)

__all__ = [
    # Navigation
    "BrowserOpenTool",
    "BrowserCloseTool",
    "BrowserNavigateTool",
    "BrowserBackTool",
    "BrowserForwardTool",
    "BrowserRefreshTool",
    "BrowserGetTitleTool",
    "BrowserGetUrlTool",
    "BrowserSearchTool",
    # Interaction
    "BrowserFindTool",
    "BrowserClickTool",
    "BrowserDoubleClickTool",
    "BrowserTypeTool",
    "BrowserClearTool",
    "BrowserSelectTool",
    "BrowserPressKeyTool",
    "BrowserScrollTool",
    "BrowserScrollToTool",
    # Tabs
    "BrowserNewTabTool",
    "BrowserSwitchTabTool",
    "BrowserCloseTabTool",
    "BrowserListTabsTool",
    # Content & Media
    "BrowserExtractTextTool",
    "BrowserExtractLinksTool",
    "BrowserSummarizeTool",
    "BrowserExtractDataTool",
    "BrowserScreenshotTool",
    "BrowserUploadFileTool",
    "BrowserDownloadFileTool",
    "BrowserPlayYouTubeTool",
]
