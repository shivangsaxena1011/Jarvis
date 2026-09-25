# SHIVANI AI — PERFORMANCE ENGINEERING & BENCHMARKING (PHASE 19)

## 1. Benchmarking Suite
The `ModelBenchmarkSuite` captures empirical performance metrics for installed local models and cloud endpoints:
- **Throughput**: Tokens per second generated during text inference.
- **TTFT (Time-to-First-Token)**: Latency from request issuance to receipt of the initial token chunk.
- **Tool-Calling Compliance**: Verifies whether the model outputs valid JSON tool calls.
- **Structured Output Compliance**: Verifies adherence to strict schema requirements.
- **Memory Footprint**: Working set RAM and dedicated GPU VRAM consumed during peak inference.

---

## 2. CLI Benchmark Execution
```bash
# Benchmark default local model (llama3.1:8b)
shivani ai benchmark

# Benchmark specific model
shivani ai benchmark --model phi3:mini
```

---

## 3. Live Metrics Tracking
Live metrics are tracked by `AIUsageMetrics` and queryable via CLI and REST:
- Request counts partitioned by Local, Cloud, and Deterministic Fast-Path.
- Cumulative input and output token consumption.
- Estimated dollar cost (USD) for cloud provider usage.
- Rolling average response latency in milliseconds.
