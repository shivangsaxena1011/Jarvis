# SHIVANI AI — CONTEXT WINDOW MANAGEMENT & COMPACTION (PHASE 19)

## 1. Token Budgets
The `ContextManager` enforces strict token budgets per inference request to prevent context overflow, reduce latency, and control API expenditure:
- Default budget: 4,096 tokens.
- Heuristic token estimation: ~4 characters per token.

---

## 2. Milestone History Compression
Long task trajectories with 10+ turns are compressed into compact, structured milestones:
- Turn 0 (Initial user objective): **Always preserved intact**.
- Middle turns (Intermediate actions): **Compacted into high-level bullet summaries**.
- Recent 3 turns: **Preserved intact** to maintain immediacy and awareness of recent observations.

### Structure of Compacted Context
```markdown
# OBJECTIVE: Refactor authentication middleware and run tests
# CURRENT STATE: Executed test suite with 4 passing tests
# COMPLETED: Modified auth.py; Added JWT validation; Ran pytest
# NEXT STEPS: Commit changes; Update documentation
[Compressed History Milestone (6 steps)]:
- [USER]: Please fix failing test in auth_test.py...
- [ASSISTANT]: Found syntax error at line 42...
- [USER]: Go ahead and fix it...
```

---

## 3. Semantic Response Caching
`SemanticCache` caches deterministic responses (math, invariant tool executions) with explicit TTLs:
- In-memory thread-safe dictionary keyed by SHA-256 of normalized prompt.
- Rejects caching any payload containing secrets, tokens, or credentials.
