# SHIVANI — GitHub Integration

## Overview
The GitHub integration (`integrations/github/service.py`) bridges local developer project spaces with remote GitHub repositories and actions.

## Features
- **Local Project Analysis**: Inspects repository layout, languages, frameworks, package managers, and safe startup commands.
- **Runnable Service Detection**: Automatically determines whether a project can be run safely (e.g. `uvicorn main:app`, `python app.py`, `npm start`), flagging any dangerous commands (e.g. deletion, remote downloads) for explicit user authorization.
- **File System Operations**: Read files, list directory structure, create branches, and prepare commits.
- **Issue Tracking**: Read issues, search issues, and draft new issues.

## Registered Tools
- `github.inspect_repository`: Inspects repository structure and detects frameworks.
- `github.read_file`: Reads file content safely within project boundaries.
- `github.list_files`: Lists repository files up to specified depth.
- `github.inspect_runnable`: Determines safe startup command and entrypoint.
- `github.read_issues`: Reads issues from repository.
- `github.create_issue`: Creates a new issue (requires user confirmation).
