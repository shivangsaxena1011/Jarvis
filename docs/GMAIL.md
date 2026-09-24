# SHIVANI — Gmail Integration

## Overview
The Gmail integration (`integrations/gmail/service.py`) provides safe, non-destructive email triage, search, categorization, executive summaries, and two-stage batch cleanup.

## Safety Principles
- **No Direct Deletion**: Bulk actions always default to `archive`. Permanent deletion requires explicit `RiskLevel.CRITICAL` authorization.
- **Two-Stage Proposal Pattern**:
  1. `gmail.cleanup_proposal` analyzes emails and presents candidates (promotions, newsletters).
  2. Workflow pauses for human approval.
  3. `gmail.execute_cleanup` executes only approved actions.
- **Read & Summarization**: Categorizes emails into `important`, `personal`, `work`, `promotional`, and `spam`.

## Registered Tools
- `gmail.open`: Navigates to Gmail inbox.
- `gmail.list_unread`: Lists recent unread emails with sender, subject, and snippet preview.
- `gmail.search`: Searches emails by query string.
- `gmail.summarize`: Summarizes unread emails with category breakdowns.
- `gmail.cleanup_proposal`: Generates a structured proposal classifying cleanup candidates.
- `gmail.execute_cleanup`: Executes approved batch actions (`archive` or `delete`).
