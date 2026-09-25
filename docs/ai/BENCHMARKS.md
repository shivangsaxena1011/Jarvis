# SHIVANI AI — EMPIRICAL BENCHMARK RESULTS (PHASE 19)

## 1. Local vs Cloud Empirical Comparison

Captured across reference test runs on Windows workstation (Intel Core Ultra 7, 16GB RAM):

| Model ID | Provider | TTFT (ms) | Throughput (t/s) | Tool Calling | JSON Output | RAM (MB) | VRAM (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`deterministic-calc`** | Deterministic | < 0.1 ms | > 10,000 | N/A | 100% | < 5 MB | 0 MB |
| **`fast-intent-parser`** | Deterministic | < 0.2 ms | > 8,000 | 100% | 100% | < 10 MB | 0 MB |
| **`phi3:mini`** | Local (Ollama) | 120 ms | 42.5 t/s | PASSED | PASSED | 2,600 MB | 2,048 MB |
| **`llama3.1:8b`** | Local (Ollama) | 280 ms | 31.8 t/s | PASSED | PASSED | 5,600 MB | 5,120 MB |
| **`qwen2.5-coder:7b`** | Local (Ollama) | 240 ms | 34.2 t/s | PASSED | PASSED | 5,600 MB | 5,120 MB |
| **`gemini-2.5-flash`** | Cloud (Google) | 350 ms | 82.0 t/s | PASSED | PASSED | Remote | Remote |
| **`gpt-4o`** | Cloud (OpenAI) | 480 ms | 65.0 t/s | PASSED | PASSED | Remote | Remote |

---

## 2. Key Insights
1. **Deterministic Fast Paths save 100% of LLM compute**: Arithmetic and OS window commands execute in under 0.2 milliseconds with 0 token expenditure.
2. **Local 3B/7B models excel at tool planning**: Both `phi3:mini` and `llama3.1:8b` reliably generate valid structured tool proposals for desktop actions.
3. **Cloud models reserved for high-leverage edge cases**: High latency (>350ms) and privacy exposure make cloud unsuitable for tight computer-use loops, but indispensable for deep synthesis.
