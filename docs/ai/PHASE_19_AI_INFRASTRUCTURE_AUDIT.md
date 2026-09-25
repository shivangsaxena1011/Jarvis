# PHASE 19: LOCAL AI, MODEL ROUTING, PERFORMANCE & OFFLINE AUTONOMY — AUDIT

## 1. Executive Summary

Shivani's intelligence stack across Phases 1–18 relied primarily on unified LLM provider abstractions (`core/providers/base.py`, `gemini.py`, `openai.py`, `ollama.py`, and `mock.py`) coupled with a basic linear fallback chain (`fallback.py`).

While functional, this earlier architecture lacked:
1. **Dynamic Task-to-Model Routing**: Simple tasks (e.g. arithmetic, opening an application window) risked invoking heavyweight general LLMs rather than fast deterministic tools or intent parsers.
2. **Privacy-Aware Data Classification**: Sending queries containing credentials or private codebase secrets to cloud providers without pre-transmission classification and redactive filtering.
3. **Hardware-Aware Local Model Execution**: No automated detection of Windows CPU, RAM, GPU vendor (NVIDIA vs AMD vs Intel vs None), or VRAM limits to safely determine whether a 3B, 7B, 14B, or 32B model can run locally without out-of-memory crashes.
4. **Resilient Offline Autonomy**: When network connectivity drops, Shivani must degrade gracefully, explicitly informing the user of internet-dependent constraints rather than hanging or hallucinating current real-time data.
5. **Specialized Multimodal Routing**: Vision, OCR, STT, and TTS lacked automated selection between local specialized engines (e.g. UI Automation accessibility tree, local Whisper, Tesseract/PaddleOCR) and cloud vision models.

Phase 19 implements an end-to-end intelligent routing, privacy, local runtime, and performance subsystem under `core/ai/`.

---

## 2. Existing AI Infrastructure Audit

| Subsystem | Existing Implementation | Identified Gaps | Phase 19 Solution |
| :--- | :--- | :--- | :--- |
| **LLM Providers** | `core/providers/` (`gemini.py`, `openai.py`, `ollama.py`, `mock.py`) | Static selection based on `.env`. No dynamic per-task model switching. | `ModelProvider` abstraction with `ProviderType` (`CLOUD`, `LOCAL`, `HYBRID`, `SPECIALIZED`, `DETERMINISTIC`). |
| **Model Registry** | Hardcoded model strings (`gemini-2.5-flash`, `gpt-4o`). | No tracking of context windows, tool-calling reliability, quantization, or hardware requirements. | Central `ModelRegistry` cataloging metadata, capabilities, context limits, and costs. |
| **Hardware Detection** | None. Assumes CUDA or arbitrary environment. | Cannot determine whether system has 8GB vs 32GB RAM, or an NVIDIA RTX vs Intel Iris GPU. | `HardwareProfile` detector inspecting Windows CPU, RAM, GPU vendor, and VRAM. |
| **Task Routing** | Single configured LLM for everything. | Expensive cloud calls for simple tasks ("What is 25 * 18?" or "Open Chrome"). | `ModelRouter` with deterministic fast paths, privacy tiers, and multi-factor model selection. |
| **Privacy & Secrets** | Basic token redaction in logs. | No classification or redactive filtering on data leaving the host machine. | `DataClassifier` and `CloudContextFilter` enforcing local execution for `CRITICAL`/`SENSITIVE` data. |
| **Fallback System** | Linear `FallbackProviderChain`. | Tries providers sequentially without understanding why a provider failed or if an offline fallback exists. | Multi-tier Fallback Chain: Primary -> Fallback 1 -> Fallback 2 -> Local Fallback -> Deterministic. |
| **Offline Autonomy** | Network drops cause tool timeouts or socket errors. | Fabricates or times out on internet-dependent tasks. | `OfflineManager` switching to degraded mode; operates local files, tools, and local models truthfully. |
| **Resource Management** | None. Concurrent model calls can exhaust VRAM. | Repeatedly loading/unloading models causes heavy latency spikes. | `ModelResourceManager` with model warming, concurrency control, and RAM/VRAM tracking. |
| **Context Management** | Raw conversation list passed to LLM. | Context blowout on long-running tasks. | `ContextManager` with token budgets, semantic history compression, and provenance preservation. |
| **Specialized Routing** | Ad-hoc selection for OCR, vision, STT, and TTS. | Vision models called when structured accessibility tree is available. | Unified specialized router: Accessibility tree -> CV -> Local Vision -> Cloud Vision. |

---

## 3. Core Architectural Posture

> **"Use the smallest reliable capability that can complete the task correctly and safely."**

```
                            USER INPUT / TASK
                                   │
                                   ▼
                     +----------------------------+
                     |  Intent & Task Classifier  |
                     +-------------+--------------+
                                   │
                 ┌─────────────────┴─────────────────┐
                 │                                   │
        [Deterministic Match]               [Requires Reasoning]
                 │                                   │
                 ▼                                   ▼
     +-----------------------+              +------------------+
     | Fast Path / Calculator|              |  Privacy & Data  |
     | or Native Tool Action |              |  Classification  |
     +-----------------------+              +--------+---------+
                                                     │
                                                     ▼
                                            +------------------+
                                            | Hardware Profile |
                                            | & Network Check  |
                                            +--------+---------+
                                                     │
                                                     ▼
                                            +------------------+
                                            |   MODEL ROUTER   |
                                            +--------+---------+
                                                     │
                     ┌───────────────────────────────┼───────────────────────────────┐
                     │                               │                               │
                     ▼                               ▼                               ▼
           +-------------------+           +-------------------+           +-------------------+
           |    LOCAL MODEL    |           |    CLOUD MODEL    |           |    SPECIALIZED    |
           | (Ollama / Llama)  |           | (Gemini / OpenAI) |           |  (Whisper / OCR)  |
           +---------+---------+           +---------+---------+           +---------+---------+
                     │                               │                               │
                     └───────────────────────────────┼───────────────────────────────┘
                                                     │
                                                     ▼
                                          +---------------------+
                                          |  Security Boundary  |
                                          |  & Tool Validation  |
                                          +----------+----------+
                                                     │
                                                     ▼
                                          +---------------------+
                                          | Verified Execution  |
                                          +---------------------+
```

---

## 4. Verification & Testing Strategy

Phase 19 verification will be conducted through test suites covering:
1. `test_model_registry_and_providers.py`: Provider abstractions, model catalog, and capability matrix.
2. `test_hardware_and_resources.py`: Hardware detection, RAM/VRAM profiling, model warming, and concurrency queue.
3. `test_model_router_and_fast_paths.py`: Fast paths, arithmetic, app commands, multi-factor scoring, and fallback chains.
4. `test_privacy_and_cloud_filter.py`: Data classification, credential scrubbing, and local-first enforcement.
5. `test_offline_autonomy.py`: Network disconnection handling, degraded truthful planning, and offline tools.
6. `test_context_and_cache.py`: Context compression, token budgets, and semantic caching.
7. `test_specialized_routing.py`: Multimodal routing (Vision vs Accessibility, OCR selection, STT/TTS).
8. `test_ai_diagnostics_and_benchmarks.py`: AI Doctor, benchmarks, and regression verification.
9. `test_ai_server_apis.py`: REST endpoints (`/api/ai/*`).
10. `test_ai_e2e_scenarios.py`: Full end-to-end integration across all 19 phases.
