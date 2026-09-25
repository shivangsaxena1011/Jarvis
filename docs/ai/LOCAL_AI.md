# SHIVANI AI — LOCAL AI & RUNTIME MANAGEMENT (PHASE 19)

## 1. Local Runtimes Supported
Shivani AI integrates with standardized local inference servers running on Windows:
- **Ollama**: Default local runtime running on `http://localhost:11434`.
- **llama.cpp / LocalAI**: OpenAI-compatible local endpoints running on `http://localhost:8080`.
- **MockLocalRuntime**: Zero-dependency deterministic local simulation for CI and headless testing.

---

## 2. Hardware Acceleration on Windows
The `HardwareProfiler` inspects the host hardware without assuming CUDA:
1. **NVIDIA GPUs**: Queries `nvidia-smi` for dedicated VRAM and CUDA driver version.
2. **AMD / Intel GPUs**: Queries Windows WMI/CIM instances (`Win32_VideoController`) for DirectX / DirectML acceleration.
3. **CPU Execution**: Allocates execution threads proportional to physical CPU cores, utilizing AVX2/AVX-512 quantization.

### Recommended Quantized Local Models
```bash
# 1. Ultra-fast lightweight model (4GB RAM)
ollama pull phi3:mini

# 2. Balanced general reasoning & tool planning (8GB RAM)
ollama pull llama3.1:8b

# 3. High-capability code synthesis (8GB RAM)
ollama pull qwen2.5-coder:7b
```

---

## 3. Memory & VRAM Governor
To prevent out-of-memory crashes on workstations with integrated GPUs:
- **Model Warming**: Pre-loads target model weights into memory before complex tasks.
- **Dynamic Eviction**: Evicts idle models after a configurable timeout (default 600s).
- **Concurrency Locking**: When running on hosts with limited VRAM, `ModelResourceManager` ensures only 1 model occupies GPU weights simultaneously, automatically unloading previous models upon switching.
- **Battery Governor**: If host laptop drops below 20% battery while unplugged, heavy local model generation is throttled or deferred.
