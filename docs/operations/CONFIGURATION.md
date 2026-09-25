# SHIVANI 1.0 Configuration Guide

## 1. Configuration File Locations
- Primary User Configuration: `%APPDATA%\Shivani\config\shivani_config.json`
- Environment Variables: Local `.env` in project root or system environment variables.
- Encrypted Secret Vault: `%APPDATA%\Shivani\data\vault.enc` (DPAPI encrypted).

---

## 2. Core Settings Overview
```json
{
  "version": "1.0.0",
  "environment": "production",
  "llm_provider": "gemini",
  "llm_model": "gemini-2.5-pro",
  "security_policy": "strict",
  "voice_enabled": false,
  "offline_mode": false,
  "host": "127.0.0.1",
  "port": 8000
}
```

### Key Parameters:
- `llm_provider`: `gemini`, `anthropic`, `openai`, `ollama`, or `hybrid`.
- `security_policy`:
  - `strict`: Requires explicit confirmation for sensitive and critical actions.
  - `standard`: Requires confirmation for high-risk and critical actions.
  - `lenient`: Requires confirmation only for critical system modifications.
- `offline_mode`: When `true`, cuts off all outbound network LLM requests; forces local model execution or fails closed.
- `voice_enabled`: Enables local streaming microphone capture and wake word detection ("Shivani" / "Jarvis").

---

## 3. Managing Secrets Securely
Never write API keys into plain JSON configuration files. Use the encrypted Secret Manager:

```powershell
# Inspect active configuration
shivani config

# Set an encrypted secret
python -c "from security.secret_manager import SecretManager; sm = SecretManager(); sm.set_secret_sync('GEMINI_API_KEY', 'your-api-key-here')"
```
