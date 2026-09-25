# SHIVANI AI — AI SUBSYSTEM CONFIGURATION REFERENCE (PHASE 19)

## 1. Environment Variables

Configure these settings in your `.env` file to customize local and cloud model behaviors:

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SHIVANI_ROUTING_STRATEGY` | String | `auto` | Default strategy: `auto`, `local_first`, `cloud_first`, `speed_first`, `cost_aware`, `privacy_first` |
| `SHIVANI_OLLAMA_BASE_URL` | String | `http://localhost:11434` | Base URL for the local Ollama inference server |
| `SHIVANI_ALLOW_CLOUD` | Boolean | `true` | Master switch to enable or completely disable external cloud calls |
| `SHIVANI_MAX_CONCURRENT_LOCAL_MODELS` | Integer | `1` | Max models loaded into memory simultaneously (recommended 1 for integrated GPUs) |
| `SHIVANI_MODEL_IDLE_TIMEOUT_SEC` | Float | `600.0` | Timeout in seconds before an idle local model is evicted from VRAM/RAM |
| `SHIVANI_CONTEXT_TOKEN_BUDGET` | Integer | `4096` | Default max token budget for reasoning context windows |

---

## 2. CLI Control Commands

```bash
# View live AI system status, hardware profile, and token usage
shivani ai status

# List cataloged models with optional filters
shivani ai models --provider local
shivani ai models --capability coding

# Evaluate model routing for a specific prompt
shivani ai route "What is 45 * 12?"
shivani ai route "Refactor this auth function" --local --privacy sensitive

# Run empirical benchmark on local model
shivani ai benchmark --model llama3.1:8b

# Run full AI Doctor health diagnostics
shivani ai doctor

# Inspect or force offline mode
shivani ai offline
shivani ai offline --force
shivani ai offline --online
```
