# SHIVANI — Productivity Integrations Architecture

Phase 5 introduces autonomous productivity integrations and cross-application workflows to SHIVANI.

## Architecture Overview

All integrations inherit from `BaseIntegration` (`integrations/base.py`) which provides:
1. **Per-Service Rate Limiting**: Token-bucket / cooldown enforcement to prevent spam or service bans.
2. **Deterministic Logging & Event Publishing**: Every invocation publishes to the centralized EventBus.
3. **Structured Fallbacks**: Resilient execution paths that support simulated responses when isolated or offline, avoiding brittle failures.
4. **Safety & Policy Separation**: Strict adherence to the `PermissionEngine` (`SAFE`, `SENSITIVE`, `CRITICAL`).

```
                              User Intent (Voice / Text)
                                         │
                                         ▼
                                   Orchestrator
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
             Task Planner                              Workflow Engine
                    │                                         │
                    ▼                                         ▼
              Tool Registry                             Tool Registry
                    │                                         │
     ┌──────────────┼──────────────┬──────────────┬───────────┴──────────┐
     ▼              ▼              ▼              ▼                      ▼
YouTubeService GmailService LinkedInService GitHubService ResearchService + ContentAgent
```

## Integrated Services

| Service | Module | Key Capabilities | Permission Level |
|---|---|---|---|
| **YouTube** | `integrations/youtube` | Search & query ranking, video playback, pause, resume, like, fullscreen | SAFE |
| **Gmail** | `integrations/gmail` | Inbox inspection, categorized executive summaries, 2-stage cleanup proposal, batch archive | SAFE (Read/Summarize), SENSITIVE (Cleanup/Archive), CRITICAL (Delete) |
| **LinkedIn** | `integrations/linkedin` | Showcase generation, DRAFT creation, user approval gate, publication verification | SAFE (Draft), CRITICAL (Publish) |
| **GitHub** | `integrations/github` | Local repository inspection, language/framework detection, safe runnable inspection, issue tracking | SAFE (Inspect/Read), SENSITIVE (Issues/PRs) |
| **Research** | `integrations/research` | Multi-source web search, structured citation extraction, synthesis, markdown/JSON bundle export | SAFE |
| **Content** | `agents/content` | Social post formatting, executive email drafts, PR comments, README synthesis | SAFE (Drafts only) |

## Rate Limits & Cooldowns
Default cooldowns configured in `core/config.py`:
- `RATE_LIMIT_COOLDOWN_SECONDS`: 1.0s (default)
- LinkedIn: 2.0s
- Gmail: 1.5s
- YouTube: 1.0s
- GitHub: 1.0s
