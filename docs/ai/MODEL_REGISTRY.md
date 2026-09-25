# SHIVANI AI — MODEL REGISTRY SPECIFICATION (PHASE 19)

## 1. Registered Model Catalog

The `ModelRegistry` maintains the canonical catalog of all inference engines available to Shivani.

| Model ID | Provider | Quantization | Context Window | Min RAM | Reasoning Score | Primary Capabilities |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`deterministic-calc`** | Deterministic | Exact | 1,024 | 4 GB | 1.00 | Arithmetic evaluation |
| **`fast-intent-parser`** | Deterministic | Regex/Rules | 2,048 | 4 GB | 0.70 | Desktop OS commands, basic queries |
| **`phi3:mini`** | Local (Ollama) | Q4_0 (3.8B) | 4,096 | 4 GB | 0.55 | Fast classification, short intent |
| **`llama3.1:8b`** | Local (Ollama) | Q4_K_M (8B) | 16,384 | 8 GB | 0.78 | General reasoning, planning, tool calling |
| **`qwen2.5:7b`** | Local (Ollama) | Q4_K_M (7B) | 32,768 | 8 GB | 0.80 | High-context conversation, tool calls |
| **`qwen2.5-coder:7b`** | Local (Ollama) | Q4_K_M (7B) | 32,768 | 8 GB | 0.82 | Local code synthesis, debugging, tests |
| **`gemini-2.5-flash`** | Cloud (Google) | Cloud API | 1,000,000 | 4 GB | 0.88 | High-speed multimodal web queries |
| **`gpt-4o`** | Cloud (OpenAI) | Cloud API | 128,000 | 4 GB | 0.94 | Complex desktop planning, creative tasks |
| **`gemini-1.5-pro`** | Cloud (Google) | Cloud API | 2,000,000 | 4 GB | 0.96 | Extreme long-context doc synthesis |
| **`whisper-local`** | Specialized | Int8 | 8,192 | 4 GB | 0.90 | Local offline speech-to-text |
| **`piper-tts-local`** | Specialized | Onnx | 8,192 | 2 GB | 0.85 | Local offline neural voice output |
| **`paddle-ocr-local`** | Specialized | Int8 | 8,192 | 4 GB | 0.88 | Local document & UI text extraction |

---

## 2. Health State Lifecycle
Each model transitions through dynamic health states managed by the registry:
- **`AVAILABLE`**: Operational and ready to service queries immediately.
- **`WARMED`**: Weights loaded in active RAM or VRAM, eliminating first-token spin-up latency.
- **`UNAVAILABLE`**: Inference daemon unreachable or API key unconfigured.
- **`DEGRADED`**: Rate limited, high latency (>5s), or intermittent connection drops.
- **`ERROR`**: Model weights corrupted or process terminated unexpectedly.

---

## 3. Dynamic Registration
Custom models can be added dynamically at runtime via the REST API or Python SDK:
```python
from core.ai.registry import ModelRegistry
from core.ai.models import ModelDescriptor, ProviderType, ModelCapability

registry = ModelRegistry()
registry.register_model(ModelDescriptor(
    model_id="mistral-nemo:12b",
    name="Mistral NeMo 12B",
    provider_id="ollama",
    provider_type=ProviderType.LOCAL,
    capabilities=[ModelCapability.SIMPLE_CONVERSATION.value, ModelCapability.CODING.value],
    context_window=32768,
    min_ram_gb=12.0,
))
```
