"""
SHIVANI Mock Web Server for Local Browser Testing
Provides local HTTP routes and DOM elements for testing all browser agent capabilities.
"""

import asyncio
from aiohttp import web


INDEX_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>SHIVANI Test Application</title>
    <meta name="description" content="Test environment for SHIVANI Universal Browser Agent" />
</head>
<body>
    <header>
        <h1>SHIVANI Test Portal</h1>
        <nav>
            <a href="/target" id="nav-target">Target Page</a>
            <a href="/download" id="download-link" download="sample.txt">Download Document</a>
        </nav>
    </header>

    <main>
        <section id="search-section">
            <h2>Search Panel</h2>
            <input type="text" id="query-input" placeholder="Search query here..." name="q" aria-label="Search Query" />
            <button id="search-btn" aria-label="Submit Search">Search Now</button>
            <div id="search-status">Ready</div>
        </section>

        <section id="form-section">
            <h2>User Form</h2>
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" placeholder="Enter username" />
            
            <label for="country">Country:</label>
            <select id="country" name="country">
                <option value="us">United States</option>
                <option value="in">India</option>
                <option value="uk">United Kingdom</option>
            </select>

            <label for="file-upload">Upload Document:</label>
            <input type="file" id="file-upload" name="upload_file" />
        </section>

        <section id="content-section">
            <h2>Article Information</h2>
            <p>Artificial Intelligence computer agents are capable of autonomous reasoning and multi-step desktop workflows.</p>
            <p>SHIVANI combines voice, vision, operating system control, and browser automation into a seamless experience.</p>
        </section>
    </main>

    <script>
        document.getElementById('search-btn').addEventListener('click', () => {
            const query = document.getElementById('query-input').value;
            document.getElementById('search-status').innerText = 'Results found for: ' + query;
        });
    </script>
</body>
</html>
"""

TARGET_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Target Destination</title>
</head>
<body>
    <h1>Destination Reached</h1>
    <p>Successfully navigated to the target page.</p>
</body>
</html>
"""

MOCK_YOUTUBE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>YouTube Mock</title>
</head>
<body>
    <input id="search" name="search_query" placeholder="Search" aria-label="Search" />
    <button id="search-icon-legacy" aria-label="Search">Search</button>

    <div id="contents">
        <div class="video-item">
            <a id="video-title" class="yt-simple-endpoint style-scope ytd-video-renderer" 
               title="Arijit Singh - Tum Hi Ho Official Song" 
               href="/watch?v=tumhiho">
               Arijit Singh - Tum Hi Ho Official Song
            </a>
        </div>
        <div class="video-item">
            <a id="video-title" class="yt-simple-endpoint style-scope ytd-video-renderer" 
               title="Arijit Singh Live Concert 2024" 
               href="/watch?v=live2024">
               Arijit Singh Live Concert 2024
            </a>
        </div>
    </div>
</body>
</html>
"""

MOCK_WATCH_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Arijit Singh - Tum Hi Ho Official Song - YouTube</title>
</head>
<body>
    <div id="player">
        <video class="html5-main-video" id="movie_player" autoplay></video>
    </div>
    <h1 class="title">Arijit Singh - Tum Hi Ho Official Song</h1>

    <script>
        const v = document.getElementById('movie_player');
        // Simulate playing video element properties
        Object.defineProperty(v, 'paused', { value: false, writable: true });
        Object.defineProperty(v, 'currentTime', { value: 12.5, writable: true });
        Object.defineProperty(v, 'readyState', { value: 4, writable: true });
    </script>
</body>
</html>
"""


class MockTestServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()
        self.runner: web.AppRunner = None
        self.site: web.TCPSite = None

    def _setup_routes(self):
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/target", self.handle_target)
        self.app.router.add_get("/download", self.handle_download)
        self.app.router.add_get("/youtube", self.handle_youtube)
        self.app.router.add_get("/watch", self.handle_watch)

    async def handle_index(self, request):
        return web.Response(text=INDEX_HTML, content_type="text/html")

    async def handle_target(self, request):
        return web.Response(text=TARGET_HTML, content_type="text/html")

    async def handle_download(self, request):
        content = "Sample download content from SHIVANI test server."
        headers = {
            "Content-Disposition": 'attachment; filename="sample.txt"'
        }
        return web.Response(text=content, content_type="text/plain", headers=headers)

    async def handle_youtube(self, request):
        return web.Response(text=MOCK_YOUTUBE_HTML, content_type="text/html")

    async def handle_watch(self, request):
        return web.Response(text=MOCK_WATCH_HTML, content_type="text/html")

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        # Retrieve actual bound port if port 0 was passed
        if self.site._server and self.site._server.sockets:
            self.port = self.site._server.sockets[0].getsockname()[1]


    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
