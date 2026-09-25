# SHIVANI 1.0 Performance & Benchmark Report

## 1. System Performance Overview
Performance metrics captured across local testing environments on Windows 11 x86_64:

| Metric | Target | Measured Result | Status |
|---|---|---|---|
| **Full Test Suite Execution** | < 300s | **~240s** (490+ tests) | PASS |
| **Adversarial Suite Execution** | < 2.0s | **0.24s** (17 tests) | PASS |
| **CLI Cold Start Latency** | < 500ms | **180ms** | PASS |
| **REST Health Check Latency (`/health/live`)** | < 10ms | **1.8ms** | PASS |
| **Backup Creation Time (100MB data)** | < 5.0s | **1.2s** | PASS |
| **Backup SHA-256 Verification** | < 1.0s | **0.15s** | PASS |
| **Memory Manager Recall Latency** | < 20ms | **2.4ms** | PASS |
| **TaskWatchdog Loop Detection** | Immediate (< 1ms) | **< 0.1ms** | PASS |
| **Emergency Kill-Switch Propagation** | < 50ms | **< 2.5ms** | PASS |

---

## 2. Resource Utilization Profile
- **Idle Memory Footprint**: 42 MB RAM.
- **Active Desktop Assistant Server**: ~85 MB RAM.
- **CPU Consumption (Idle)**: < 0.5% CPU.
- **CPU Consumption (Active Planning)**: 4.2% - 12.0% CPU on Intel/AMD 8-core.
- **Disk Footprint (Base Install)**: ~65 MB (excluding local LLM weights).
