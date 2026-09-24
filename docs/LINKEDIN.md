# SHIVANI — LinkedIn Integration

## Overview
The LinkedIn integration (`integrations/linkedin/service.py`) automates social project showcases, updates, and interactions while strictly enforcing human-in-the-loop safety.

## DRAFT vs. PUBLISHED Lifecycle
1. `content.generate_linkedin_post`: Synthesizes engaging post copy with project highlights, tech tags, and hooks.
2. `linkedin.prepare_post`: Saves the post in `DRAFT` state with an assigned draft ID (`li_post_<uuid>`).
3. **Approval Gate**: Publication is marked `RiskLevel.CRITICAL`. The agent pauses and requests explicit user approval.
4. `linkedin.publish_post`: Only after approval is confirmed does the post transition to `PUBLISHED`.

## Registered Tools
- `linkedin.open`: Navigates to LinkedIn feed.
- `linkedin.prepare_post`: Prepares post draft.
- `linkedin.publish_post`: Publishes draft to LinkedIn (requires confirmation).
- `linkedin.search`: Searches LinkedIn posts, people, or companies.
