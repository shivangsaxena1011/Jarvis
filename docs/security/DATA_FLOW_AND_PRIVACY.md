# SHIVANI Data Flow & Privacy Architecture

## 1. Data Classification Tiers
1. **Public**: Public information, general web search queries, public documentation lookups. Routed to cloud models (Gemini / Anthropic / OpenAI) without restriction.
2. **Internal / Low Sensitivity**: Project outlines, public repository code, impersonal task lists.
3. **Private**: Personal schedule, contact names, task descriptions, personal knowledge notes. Encrypted at rest.
4. **Sensitive**: Financial documents, personal health notes, passwords, private emails, chat logs. Routed exclusively to local offline models or masked.
5. **Critical**: API keys, credentials, recovery phrases, authentication secrets. NEVER sent to any LLM (local or cloud). Stored exclusively via Windows DPAPI.

---

## 2. Model Routing & Zero-Leakage Privacy Policy
When the user or task requests model execution:
1. `ModelRouter` evaluates the data classification tier and active `PrivacyPolicy`.
2. If `OfflineMode` is active or privacy tier is `CRITICAL`/`SENSITIVE`, the router forces local model inference (e.g. Ollama local LLM) or deterministic rules.
3. If no capable local model exists and cloud transmission is prohibited by policy, the operation fails-closed with `PrivacyViolationError` rather than leaking user data.

---

## 3. Data Governance & GDPR Compliance
- **Data Export (`shivani data export`)**: Generates portable, standardized JSON/ZIP exports of the user's memories, knowledge graphs, and goals.
- **Zero-Trace Wipe (`shivani data delete`)**: Cryptographically and physically purges SQLite databases (`memory.db`, `knowledge.db`), caches, audio transcripts, and task histories upon explicit confirmation (`confirm=True`).
- **Secret Redaction**: All text entering episodic or short-term memory is pre-filtered by `SecretRedactor` regex filters to eliminate API keys, bearer tokens, and passwords from logs and vector stores.
