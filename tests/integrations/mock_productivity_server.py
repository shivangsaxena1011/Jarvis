"""
SHIVANI Mock Productivity Web Server
Provides local HTTP routes and HTML DOM structures for testing YouTube,
Gmail, LinkedIn, GitHub, and Research integrations.
"""

from aiohttp import web

MOCK_YOUTUBE_SEARCH_HTML = """<!DOCTYPE html>
<html>
<head><title>YouTube</title></head>
<body>
    <div id="contents">
        <div class="video-item">
            <a id="video-title" class="yt-simple-endpoint style-scope ytd-video-renderer"
               title="Heart Disease Prediction Machine Learning Project Full Walkthrough"
               href="/watch?v=hdml101">Heart Disease Prediction Machine Learning Project Full Walkthrough</a>
            <span class="channel-name">AI CodeLab Official</span>
            <span class="metadata">150K views</span>
        </div>
        <div class="video-item">
            <a id="video-title" class="yt-simple-endpoint style-scope ytd-video-renderer"
               title="Arijit Singh Best Songs 2024"
               href="/watch?v=arijit2024">Arijit Singh Best Songs 2024</a>
            <span class="channel-name">T-Series</span>
            <span class="metadata">5M views</span>
        </div>
    </div>
</body>
</html>
"""

MOCK_GMAIL_INBOX_HTML = """<!DOCTYPE html>
<html>
<head><title>Gmail - Inbox</title></head>
<body>
    <div role="main">
        <div class="email-row" data-id="m1" data-unread="true">
            <span class="sender">Security Alert &lt;no-reply@accounts.google.com&gt;</span>
            <span class="subject">New sign-in from Windows Desktop</span>
            <span class="snippet">Your Google Account was accessed from a new device...</span>
            <span class="badge important">Important</span>
        </div>
        <div class="email-row" data-id="m2" data-unread="true">
            <span class="sender">Prof. Sharma &lt;sharma@university.edu&gt;</span>
            <span class="subject">Project Review Meeting Tomorrow</span>
            <span class="snippet">Please bring your updated system design documentation...</span>
            <span class="badge work">Work</span>
        </div>
        <div class="email-row" data-id="m3" data-unread="true">
            <span class="sender">TechFlash Newsletter &lt;news@techflash.io&gt;</span>
            <span class="subject">Top 10 AI Frameworks This Week</span>
            <span class="snippet">Discover the latest advancements in LLM agent tool calling...</span>
            <span class="badge newsletter">Newsletter</span>
        </div>
        <div class="email-row" data-id="m4" data-unread="true">
            <span class="sender">SuperShop Deals &lt;deals@supershop.xyz&gt;</span>
            <span class="subject">Mega Sale: Up to 80% off today only!</span>
            <span class="snippet">Don't miss our exclusive clearance discount coupons...</span>
            <span class="badge promo">Promotional</span>
        </div>
    </div>
</body>
</html>
"""

MOCK_LINKEDIN_FEED_HTML = """<!DOCTYPE html>
<html>
<head><title>Feed | LinkedIn</title></head>
<body>
    <div id="feed-container">
        <div class="feed-shared-update-v2" data-urn="urn:li:activity:101">
            <span class="update-components-actor__name">Satya Nadella</span>
            <div class="feed-shared-update-v2__description">
                AI agents are transforming how every developer and organization builds software.
            </div>
        </div>
        <div class="feed-shared-update-v2" data-urn="urn:li:activity:102">
            <span class="update-components-actor__name">Yann LeCun</span>
            <div class="feed-shared-update-v2__description">
                World models and autonomous planning are essential steps beyond autoregressive token prediction.
            </div>
        </div>
    </div>
</body>
</html>
"""

MOCK_RESEARCH_SOURCE_HTML = """<!DOCTYPE html>
<html>
<head><title>Autonomous AI Agent Architecture and Tool Orchestration</title></head>
<body>
    <article>
        <h1>Autonomous AI Agent Architecture and Tool Orchestration</h1>
        <p class="author">Dr. A. Turing, Stanford AI Lab (2024)</p>
        <div class="content">
            Recent breakthroughs in agentic runtime systems demonstrate that grounding language models
            with verified tool execution, strict safety boundaries, and observable state machines drastically
            reduces hallucination and ensures enterprise-grade reliability in autonomous workflows.
        </div>
    </article>
</body>
</html>
"""


class MockProductivityServer:
    """Lightweight test server for productivity integrations."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()
        self.runner: web.AppRunner = None
        self.site: web.TCPSite = None

    def _setup_routes(self):
        self.app.router.add_get("/youtube", self.handle_youtube)
        self.app.router.add_get("/gmail", self.handle_gmail)
        self.app.router.add_get("/linkedin", self.handle_linkedin)
        self.app.router.add_get("/research/paper1", self.handle_research_paper)

    async def handle_youtube(self, request):
        return web.Response(text=MOCK_YOUTUBE_SEARCH_HTML, content_type="text/html")

    async def handle_gmail(self, request):
        return web.Response(text=MOCK_GMAIL_INBOX_HTML, content_type="text/html")

    async def handle_linkedin(self, request):
        return web.Response(text=MOCK_LINKEDIN_FEED_HTML, content_type="text/html")

    async def handle_research_paper(self, request):
        return web.Response(text=MOCK_RESEARCH_SOURCE_HTML, content_type="text/html")

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        if self.site._server and self.site._server.sockets:
            self.port = self.site._server.sockets[0].getsockname()[1]

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
