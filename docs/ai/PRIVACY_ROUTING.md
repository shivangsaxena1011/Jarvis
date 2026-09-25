# SHIVANI AI — PRIVACY-AWARE DATA CLASSIFICATION & ZERO-CLOUD BOUNDARY (PHASE 19)

## 1. Privacy Tiers

Every input, query, prompt, and file is analyzed by the `DataClassifier` before routing:

| Tier | Characteristics | Routing Constraint |
| :--- | :--- | :--- |
| **`CRITICAL`** | API keys, private keys, passwords, credentials, credit cards, `.env` files | **Zero-Cloud Enforcement**: Must execute exclusively on local models. Cloud transmission triggers an immediate `PermissionError`. |
| **`SENSITIVE`** | Financial records, salaries, medical data, tax returns, personal identification | Local models preferred. Cloud allowed only with explicit user override and automatic secret scrubbing. |
| **`PRIVATE`** | Local user documents, private notes, local filesystem metadata | Local models preferred. |
| **`LOW_SENSITIVITY`**| Generic coding assistance, tool operations without personal context | Routed according to standard strategy (`AUTO`). |
| **`PUBLIC`** | General public queries (math, definitions, public news, documentation) | Eligible for all tiers including cloud. |

---

## 2. Cloud Context Sanitization
The `CloudContextFilter` protects against accidental leakage:
```python
sanitized_text, was_redacted = CloudContextFilter.sanitize_for_cloud(
    text=prompt,
    privacy_level=detected_privacy,
    allow_cloud=is_cloud_allowed,
)
```
- If `privacy_level == PrivacyLevel.CRITICAL`, an uncatchable security boundary exception is raised.
- If lower sensitivity, any accidental token pattern matching `sk-...`, `ghp_...`, or Bearer keys is replaced with `***REDACTED_SECRET***`.
