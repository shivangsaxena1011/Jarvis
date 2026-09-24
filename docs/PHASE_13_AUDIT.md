# SHIVANI — Comprehensive Phase 13 Universal Skills & Extensibility Audit

**Date**: September 24, 2026  
**Auditor**: Principal Autonomous Systems & Extensibility Architect  
**Scope**: Universal Skills Architecture, Plugin System, Connectors, App Adapters, Capability Marketplace, Sandbox, and Skill Lifecycle  
**Baseline**: Phase 12 Verified (`8877234`, 255/255 Passing Tests across 52 test suites, 159 Registered Tools)

---

## 1. Executive Summary

Phases 1 through 12 established SHIVANI as an autonomous computer-use assistant with computer control, browser automation, phone integration, vision/OCR, agentic planning, multi-agent orchestration, recovery, security, and a Personal Knowledge OS.

However, SHIVANI's capabilities currently operate as a **monolithic hardcoded assembly**:
- Every tool is hardcoded inside `tools/` and registered during orchestrator startup.
- Adding a new integration or application interaction requires modifying core runtime files (`orchestrator.py`, `ToolRegistry`, imports).
- There is no isolated lifecycle (install, enable, disable, update, uninstall) for third-party or user-created capabilities.
- Third-party code cannot be sandboxed or restricted by fine-grained resource and permission limits.
- External service accounts lack multi-account management (e.g. personal vs. work GitHub).
- The planner relies on hardcoded agent names rather than discovering dynamically available capabilities.

Phase 13 introduces the **Universal Skills & Extensibility Architecture**:
1. **Skill System (`skills/`)**: Declarative manifests, life-cycle manager (DISCOVERED, VALIDATING, INSTALLING, INSTALLED, ENABLED, DISABLED, UPDATING, FAILED, UNINSTALLING), validator, dependency resolver, semantic versioning, and isolated storage.
2. **Skill Sandbox & Security Scanner (`skills/sandbox/`)**: Static code scanning against dangerous subprocesses, token theft, network exfiltration, filesystem traversal, plus runtime execution containment.
3. **Connector Abstraction (`connectors/`)**: Standardized interfaces (`connect`, `disconnect`, `health`, `rate_limit`) with OAuth and an `AccountManager` supporting multiple accounts per provider.
4. **App Adapters (`adapters/`)**: Structured descriptors for applications (e.g. VS Code, Chrome, Terminal, Android apps) with native UI automation and generic computer vision fallbacks.
5. **Capability-Driven Planning**: Dynamic capability matching, universal action models (`DISCOVER`, `READ`, `CREATE`, `UPDATE`, `DELETE`, `EXECUTE`, `VERIFY`), and user-created skill workflows.

---

## 2. Existing System Inspection

### 2.1 Existing Tools (159 Tools in `tools/`)
- **Filesystem Tools** (`tools/filesystem/file_tools.py`): `filesystem.list`, `filesystem.read`, `filesystem.write`, `filesystem.search`, `filesystem.metadata`, `filesystem.create_dir`.
- **Computer & Window Tools** (`tools/computer/`, `tools/desktop/`): `computer.screenshot`, `desktop.active_window`, `desktop.list_windows`, `desktop.open_app`, `desktop.close_app`, `input.click`, `input.type`, etc.
- **Browser Tools** (`tools/browser/`): 22 browser tools (`browser.open`, `browser.click`, `browser.extract_text`, `browser.summarize`, etc.).
- **Phone Tools** (`tools/android/`): 14 device bridge tools (`android.tap`, `android.type`, `android.launch_app`, `android.transfer_file`, etc.).
- **Integration Tools** (`tools/integrations/`): YouTube, Gmail, LinkedIn, GitHub, Research.
- **Memory & Planner Tools** (`tools/memory/`, `tools/scheduler/`, `tools/notifications/`): Preference get/set, search, forget, cron scheduling, notifications.
- **Knowledge OS Tools** (`tools/knowledge_tools.py`): `knowledge.search`, `knowledge.get_project_context`, `knowledge.index_path`, `knowledge.query_graph`, `knowledge.add_note`.

### 2.2 Existing Agents (`agents/` & `core/agents/registry.py`)
- Subagents: `ComputerAgent`, `BrowserAgent`, `CodingAgent`, `ResearchAgent`, `PresentationAgent`, `DocumentationAgent`, `PhoneAgent`, `ContentAgent`.
- Current routing: `AgentRegistry.match_agent()` uses keyword heuristics to select a fixed agent.
- Gap: Cannot route to dynamically installed third-party agents or composable skills.

### 2.3 Existing Integrations (`integrations/`)
- Services: `GmailService`, `GitHubService`, `LinkedInService`, `YouTubeService`, `ResearchService`.
- Base: `BaseIntegration` provides simple rate limiting and a single `_active_account` string.
- Gap: No standardized OAuth token management, no multi-account context (work vs. personal), no structured health check contract.

### 2.4 Existing Workflows (`core/workflows/`)
- Models: `Workflow`, `WorkflowStep`, `WorkflowResult`, `WorkflowStatus`.
- Engine: `WorkflowEngine` executes steps sequentially or with approval gates.
- Recipes: `CrossAppRecipes` provides hardcoded multi-app chains.
- Gap: No declarative YAML/JSON DSL for user-created custom skills.

### 2.5 Existing Permission Model (`security/permissions/`)
- `PermissionEngine`: Three-tier/five-tier risk classification (`SAFE`, `LOW_RISK`, `SENSITIVE`, `HIGH_RISK`, `CRITICAL`), session preapprovals, approval futures.
- Policy: `strict`, `standard`, `lenient`.
- Gap: Permissions are currently assigned on a per-tool level. Skills need declarative manifests listing requested permissions (e.g. `github.read`, `filesystem.write`), permission diffing during updates, and zero silent escalation.

### 2.6 Existing Configuration (`core/config/`)
- `Settings`: Pydantic BaseSettings loading `.env`.
- `AppDirectories`: Standard directories (`root`, `config`, `data`, `logs`, `memory`, `tasks`, `cache`, `backups`).
- Gap: Skills need their own isolated directory `%APPDATA%\Shivani\skills\<skill_name>\` for configurations, caches, logs, and secrets.

---

## 3. Reusable Components & Extensibility Gaps

| Component | Current State | Reusability in Phase 13 |
| :--- | :--- | :--- |
| `ToolRegistry` | Static registration only | Reusable; add `unregister()`, skill namespace mapping, and dynamic tool lifecycle |
| `AgentRegistry` | Fixed subagents | Reusable; add dynamic agent registration and skill agent unregistration |
| `PermissionEngine` | Authoritative risk policy | Reusable as ultimate arbiter; add granular skill permission manifests & diffing |
| `SecretManager` | Secure credentials storage | Reusable; skills must access tokens via `SecretManager`, never plain text |
| `CommandValidator` | Blocks dangerous shell commands | Reusable inside `PluginSecurityScanner` and skill sandbox |
| `AppDirectories` | Standard application layout | Reusable; add `skills_dir` property for isolated skill folders |
| `WorkflowEngine` | Step execution with checkpoints | Reusable; add Skill Workflow DSL parser |

---

## 4. Phase 13 Target Architecture

```
                         SHIVANI CORE
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
    ORCHESTRATOR          KNOWLEDGE OS           SECURITY
        │                     │                      │
        └──────────────┬──────┴──────────────┬───────┘
                       │                     │
                  CAPABILITY LAYER       PERMISSIONS
                       │
              ┌────────┼────────┐
              │        │        │
            SKILLS  CONNECTORS ADAPTERS
              │        │        │
              └────────┼────────┘
                       │
                  TOOL REGISTRY
                       │
                    EXECUTION
                       │
                  VERIFICATION
```

---

## 5. Migration & Phased Rollout Plan

1. **Core Extensibility Framework (`skills/`)**:
   - `manifest.py`: Typed manifest schema with capabilities, permissions, risk tiers, and dependencies.
   - `validator.py`: Strict schema validation, semver parsing, entrypoint inspection.
   - `dependency_resolver.py`: Dependency graph, circular dependency detection, version conflict checks.
   - `permissions.py`: Granular permission mapping, permission diffing, policy validation.
   - `security_scanner.py`: Static code analyzer detecting obfuscation, secret theft, suspicious network/subprocess calls.
   - `sandbox.py`: Isolated skill execution environment with resource policies.
   - `lifecycle.py`: State machine (DISCOVERED $\rightarrow$ VALIDATING $\rightarrow$ INSTALLING $\rightarrow$ INSTALLED $\rightarrow$ ENABLED $\rightarrow$ DISABLED $\rightarrow$ FAILED $\rightarrow$ UNINSTALLING).
   - `registry.py`: Central `SkillRegistry` managing installed, enabled, and available skills.
   - `generator.py`: Generates custom user skills from natural language specifications.

2. **Connectors & Multi-Account Architecture (`connectors/`)**:
   - `base.py`: Abstract `Connector` with `connect`, `disconnect`, `health`, and rate limiting.
   - `accounts.py`: `AccountManager` handling multi-account context (e.g. GitHub personal vs. work) without exposing secrets.
   - `registry.py`: `ConnectorRegistry` tracking connector states and health metrics.

3. **Application Adapters (`adapters/`)**:
   - `base.py`: Abstract `AppAdapter` with detection rules, UI patterns, operations, and verification.
   - `discovery.py`: Discovers installed Windows/desktop applications.
   - `windows.py`, `browser.py`, `android.py`: Core application adapters (VS Code, Chrome, etc.) with computer-use vision fallback.

4. **Integration & Orchestration Upgrades**:
   - Connect `SkillRegistry` with `ToolRegistry` and `AgentRegistry`.
   - Upgrade Orchestrator and Planner to query available capabilities rather than hardcoding agent names.
   - Implement CLI skill management commands (`shivani skill list`, `install`, `enable`, `disable`, `update`, `uninstall`, `info`).

5. **Testing & Verification**:
   - Manifest validation, lifecycle transitions, dependency resolution, sandbox enforcement, malicious skill detection, update permission diffs, multi-account routing, and cross-skill workflows.
   - Full regression across all 255 existing tests.
