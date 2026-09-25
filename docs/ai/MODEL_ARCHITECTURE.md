# SHIVANI AI — MODEL ARCHITECTURE & INFERENCE TIERING (PHASE 19)

## Executive Summary
Shivani AI Phase 19 implements an intelligent, multi-tier execution paradigm that eliminates unnecessary cloud calls and establishes an unyielding privacy perimeter. The architectural principle governing all reasoning is:

> **"Use the smallest reliable capability that can complete the task correctly and safely."**

---

## 1. Multi-Tier Execution Hierarchy

```
                    ┌─────────────────────────┐
                    │   User Request / Goal   │
                    └────────────┬────────────┘
                                 │
                     [1. Deterministic Check]
                    ┌────────────┴────────────┐
             Yes ───►  Arithmetic / OS Intent │ ──► Deterministic Fast Path (0ms LLM, 100% exact)
                    └────────────┬────────────┘
                               No│
                    [2. Privacy Classifier]
                    ┌────────────┴────────────┐
        CRITICAL ───► Credentials / Secrets   │ ──► Local Model Only (Zero Cloud Transmission)
                    └────────────┬────────────┘
                                 │
                   [3. Multi-Factor Router]
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼
┌──────────────┐         ┌──────────────┐            ┌──────────────┐
│  Local Model │         │  Specialized │            │  Cloud Model │
│ (3B / 7B/8B) │         │ (OCR/STT/TTS)│            │(Gemini/Claude│
│   (Offline)  │         │  (Low VRAM)  │            │  /GPT-4o)    │
└──────────────┘         └──────────────┘            └──────────────┘
```

### Tier 0: Deterministic Fast Paths
- **Mathematical Evaluation**: Queries matching arithmetic patterns (`calculate 45 * (12 + 8)`) route directly to Python's deterministic math evaluator without invoking neural networks.
- **Desktop Intent Fast Path**: Common window, application, or cursor actions (`open chrome`, `take screenshot`, `close window`) match against regular expressions and invoke tool actions directly.

### Tier 1: Local Quantized Models (Air-Gapped & Offline)
- **`phi3:mini` (3.8B, Q4_0)**: 4GB RAM footprint. Instant intent classification, short summarization, and ultra-low latency fallback.
- **`llama3.1:8b` (8B, Q4_K_M)**: 8GB RAM footprint. Multi-step tool planning, structured JSON generation, private document reasoning.
- **`qwen2.5-coder:7b` (7B, Q4_K_M)**: 8GB RAM footprint. Synthesizes scripts, fixes failing tests, analyzes git diffs locally.

### Tier 2: Specialized Local Engines
- **Vision**: Prefers Windows UIAutomation Accessibility Trees; falls back to local LLaVA / Florence-2 if screen understanding is required.
- **OCR**: Prefers local PaddleOCR/Tesseract for printed text; cloud vision OCR only for low-contrast handwritten manuscripts.
- **Speech**: Local Faster-Whisper (STT) and Piper-TTS (TTS) for private offline voice pipelines.

### Tier 3: Frontier Cloud Models
- Invoked **only** when permitted by privacy policy, when internet connectivity is verified, and when high-complexity reasoning (e.g. cross-repository refactors, doctoral research synthesis) exceeds local model capabilities.

---

## 2. Model Security Barrier
Models are **untrusted reasoning engines**, never execution authorities.
```
Model Output ──► Structured Parsing ──► Security Barrier ──► User Permission ──► Execution
```
1. Model generates proposed tool calls (JSON).
2. Arguments are validated against dangerous patterns (`rm -rf`, disk formats).
3. Permissions engine checks authorization level.
4. Execution occurs in sandbox or OS adapter with idempotency and audit logs.
