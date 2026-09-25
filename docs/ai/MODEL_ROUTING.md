# SHIVANI AI — MULTI-FACTOR MODEL ROUTING (PHASE 19)

## 1. Routing Strategy Matrix

Shivani evaluates multiple operational vectors to select the optimal inference target:

$$\text{Total Score} = S_{\text{Capability}} + S_{\text{Strategy}} + S_{\text{Privacy}} - C_{\text{Cost}} - L_{\text{LatencyPenalty}}$$

### Supported Strategies
1. **`AUTO` (Default)**: Automatically balances latency, capability, cost, and privacy. Chooses deterministic tools when possible, local models for low/medium tasks, and cloud for high-complexity prompts.
2. **`LOCAL_FIRST`**: Strongly prefers local inference (`+40.0` weight bonus). Routes to cloud only when a required capability is strictly unavailable locally.
3. **`CLOUD_FIRST`**: Prefers cloud models (`+25.0` weight bonus) for maximum reasoning power and output eloquence, provided privacy checks pass.
4. **`SPEED_FIRST`**: Prioritizes lowest TTFT (Time to First Token) and highest throughput (tokens/sec). Favors `fast-intent-parser` and `phi3:mini`.
5. **`COST_AWARE`**: Zero marginal API cost strategy. Heavily penalizes cloud API token consumption.
6. **`PRIVACY_FIRST`**: Disables cloud routing unconditionally. All tasks execute locally or fail gracefully.

---

## 2. Decision Tree Flow

```
                      [User Prompt]
                            │
               [Arithmetic or OS Intent?]
                     ├────────► YES: Deterministic Engine (0ms LLM)
                     │
                    NO
                     ▼
          [Data Privacy Classification]
                     ├────────► CRITICAL: Enforce Local Engine Only
                     │
              PUBLIC / LOW
                     ▼
             [Network Reachable?]
                     ├────────► NO: Enforce Local Engine Only
                     │
                    YES
                     ▼
             [Candidate Matrix Evaluation]
          Filter by Required Capabilities & RAM
                     │
                     ▼
             [Multi-Factor Scoring]
          Select Best Candidate & Fallback Model
```

---

## 3. Fallback Chains
Every routing decision generates a primary and fallback model ID:
- Primary: `llama3.1:8b` ──(Runtime Failure)──► Fallback: `phi3:mini`
- Primary: `gpt-4o` ────────(Rate Limit / 5xx)──► Fallback: `llama3.1:8b`
- Primary: `gemini-2.5-flash` ─(Network Drop)──► Fallback: `qwen2.5-coder:7b`
