# SHIVANI — Universal Browser Agent (Phase 4)

## Overview

The **Universal Browser Agent** empowers SHIVANI to autonomously navigate, inspect, and operate web applications through real headless or headed browser sessions via **Playwright**.

SHIVANI strictly abides by the foundational operational principle:
```
OBSERVE ──▶ PLAN ──▶ ACT ──▶ VERIFY
```
SHIVANI **never blindly clicks arbitrary pixel coordinates**. Every interaction is mediated through structured DOM evaluation, accessibility tree analysis, natural-language element resolution, and explicit outcome verification.

---

## Architecture & Subsystems

```
                                      ┌─────────────────────────────────┐
                                      │       SHIVANI Orchestrator      │
                                      └────────────────┬────────────────┘
                                                       │
                                            ┌──────────▼──────────┐
                                            │    BrowserAgent     │
                                            └────┬────────────┬───┘
                 ┌───────────────────────────────┘            └──────────────────────────────┐
                 │                                                                           │
        ┌────────▼─────────┐                                                        ┌────────▼─────────┐
        │  BrowserManager  │                                                        │ BrowserWorkflows │
        │  Playwright Core │                                                        │ YouTube / Search │
        │  Channel Choice  │                                                        │ Summarize / Data │
        └────────┬─────────┘                                                        └──────────────────┘
                 │
       ┌─────────┴─────────┐
       │                   │
┌──────▼──────┐     ┌──────▼──────┐
│ PageObserver│     │ElementResolv│
│ DOM / A11y  │     │ 7-Tier Res. │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 │
      ┌──────────▼──────────┐
      │BrowserActionExecutor│
      │ Click/Type/Scroll/DL│
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │   BrowserVerifier   │
      │ URL/State/Playback  │
      └─────────────────────┘
```

### 1. `BrowserManager` (`agents/browser/manager.py`)
- Manages Playwright lifecycle with Windows Proactor Event Loop compatibility.
- Supports multi-channel launch with automatic fallback: `chrome` ➔ `msedge` ➔ `brave` ➔ bundled `chromium`.
- Isolates user profiles via `BrowserProfileManager`.
- Manages multi-tab lifecycles: open, switch, close, and list tabs with state preservation.

### 2. `PageObserver` (`agents/browser/observer.py`)
Gathers structured environmental observations before executing any action:
- **Title and URL**: Document state and location.
- **Headings**: `h1`, `h2`, `h3` hierarchy for quick semantic understanding.
- **Visible Text**: Sanitized, noise-filtered readable content.
- **Interactive Elements**: Buttons, inputs, textareas, selects, and links with roles, labels, and candidate selectors.
- **Forms**: Detected form fields and submission targets.

### 3. `ElementResolver` (`agents/browser/resolver.py`)
Implements a 7-tier natural language element resolution pipeline:
1. **ARIA Role & Name**: `get_by_role(role, name=...)`
2. **Accessible Label**: `get_by_label(description)`
3. **Placeholder**: `get_by_placeholder(description)`
4. **Attributes / Test ID**: `get_by_test_id`, `name`, `id` attributes
5. **Exact & Substring Visible Text**: `get_by_text(description)`
6. **Semantic CSS / XPath Selectors**: Heuristic selector scoring
7. **Multimodal Vision Fallback**: Coordinates via `VisionProvider` when DOM queries fail.

### 4. `BrowserActionExecutor` (`agents/browser/actions.py`)
Executes verified atomic DOM interactions:
- `click`, `double_click`
- `type_text` (with automatic pre-clearing and optional Enter press)
- `clear_input`
- `select_option`
- `press_key`
- `scroll` & `scroll_to`
- `upload_file`
- `download_file` (with custom destination path and disk verification)
- `capture_screenshot`

### 5. `BrowserVerifier` (`agents/browser/verifier.py`)
Verifies environmental outcomes after every action:
- **Navigation Verification**: URL change, expected domain match, load state.
- **Search Verification**: Results element count and selector matching.
- **Media Playback Verification**: Queries HTML5 video element state: `paused`, `currentTime > 0`, `duration`, `readyState > 2`.
- **Download Verification**: Confirms file presence and non-zero byte size on disk.

---

## Autonomous Workflows (`agents/browser/workflows.py`)

### 1. YouTube Search & Playback
- **Intent**: *"Shivani, Arijit Singh ka song search karo"* or *"Shivani, play Arijit Singh Tum Hi Ho"*.
- **Workflow**:
  1. Navigates to YouTube.
  2. Types search query into search input.
  3. Extracts top candidate video renderers.
  4. Disambiguates best candidate using `difflib.SequenceMatcher` title similarity + query word overlap boost.
  5. Clicks selected video and triggers playback.
  6. Verifies that HTML5 video state is playing (`is_playing: True`, `currentTime > 0`).

### 2. Multi-Engine Web Search
- **Engines Supported**: Google, Bing, DuckDuckGo.
- **Workflow**: Navigates to query URL, waits for result containers (`div.g`, `li.b_algo`, `.result`), parses titles, URLs, and snippet previews.

### 3. Webpage Summarization
- **Workflow**: Strips layout boilerplate (`<nav>`, `<header>`, `<footer>`, `<script>`, `<style>`, ads), extracts key headings, calculates clean text, and generates a structured summary with character metrics.

### 4. Structured Data Extraction
- **Workflow**: Collects structured headings, internal/external hyperlinks, tables, and listings into structured dictionaries.

---

## Third-Party Integrations (`integrations/`)

### LinkedIn Helper (`integrations/linkedin/linkedin_helper.py`)
- Navigates to LinkedIn feed.
- Inspects authentication state; halts and advises user if login is required.
- Prepares draft posts.
- **Security Policy**: Strictly prohibits automated publishing without explicit `CRITICAL` risk approval.

### Gmail Helper (`integrations/gmail/gmail_helper.py`)
- Navigates to Gmail inbox.
- Inspects inbox for unread email threads and message snippets.
- Executes searches via the top search bar.
- Prevents destructive message actions (sending, deleting, bulk archiving) without permission.

---

## Registered Tool Reference

All browser tools are registered under the `browser.*` namespace:

| Tool Name | Risk Level | Description |
|---|---|---|
| `browser.open` | SAFE | Launch browser and navigate to initial URL |
| `browser.close` | SAFE | Close browser session and release resources |
| `browser.navigate` | SAFE | Navigate active tab to specified URL |
| `browser.back` | SAFE | Go back in browsing history |
| `browser.forward` | SAFE | Go forward in browsing history |
| `browser.refresh` | SAFE | Reload active webpage |
| `browser.get_title` | SAFE | Get title of active webpage |
| `browser.get_url` | SAFE | Get current active URL |
| `browser.search` | SAFE | Search web using Google, Bing, or DuckDuckGo |
| `browser.find` | SAFE | Locate element using 7-tier natural language resolver |
| `browser.click` | SAFE | Click interactive button, link, or element |
| `browser.double_click` | SAFE | Double-click element |
| `browser.type` | SAFE | Type text into input field |
| `browser.clear` | SAFE | Clear input field content |
| `browser.select` | SAFE | Select dropdown option |
| `browser.press_key` | SAFE | Press keyboard key (e.g. Enter, Escape) |
| `browser.scroll` | SAFE | Scroll page up or down |
| `browser.scroll_to` | SAFE | Scroll to pixel coordinates |
| `browser.new_tab` | SAFE | Open new tab |
| `browser.switch_tab` | SAFE | Switch active tab by ID or index |
| `browser.close_tab` | SAFE | Close tab |
| `browser.list_tabs` | SAFE | List all open tabs and titles |
| `browser.extract_text` | SAFE | Extract visible text from page or selector |
| `browser.extract_links` | SAFE | Extract hyperlinks from page |
| `browser.summarize` | SAFE | Summarize active webpage content |
| `browser.extract_data` | SAFE | Extract structured data and listings |
| `browser.screenshot` | SAFE | Capture browser screenshot to disk |
| `browser.upload_file` | SENSITIVE | Upload local file to file input (requires audit/permission) |
| `browser.download_file` | SAFE | Download file to disk and verify |
| `browser.play_youtube` | SAFE | Full YouTube search, selection, and playback flow |

---

## Security & Safety Mandates

1. **Zero Credential Leakage**:
   - The browser profile manager treats cookies and session data as opaque disk artifacts.
   - Authentication secrets, passwords, and tokens are never logged to `audit.jsonl` or stored in agent context.
2. **Sensitive Action Protection**:
   - Social publishing (e.g. LinkedIn) and email sending are marked `CRITICAL` or `SENSITIVE` and require explicit user approval.
3. **Anti-Bot & Defenses Compliance**:
   - SHIVANI never bypasses CAPTCHA, MFA, rate limits, or anti-bot protections.
   - If an auth wall or CAPTCHA appears, the agent notifies the user to intervene in the browser.
