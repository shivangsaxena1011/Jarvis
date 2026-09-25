# SHIVANI AI — OFFLINE AUTONOMY & TRUTHFUL DEGRADATION (PHASE 19)

## 1. The Offline Autonomy Principle

> **"When disconnected from the internet, Shivani becomes less capable, never less truthful."**

Shivani must never fabricate, extrapolate, or hallucinate real-time external data (e.g. current stock prices, live weather, unindexed web pages) when the network is unavailable.

---

## 2. Network State Detection
The `OfflineManager` maintains real-time connectivity status:
- Periodically verifies low-level socket connectivity to public DNS (`1.1.1.1:53` / `8.8.8.8:53`) with a 1-second timeout.
- Supports forced offline simulation (`shivani ai offline --force`) for testing air-gapped environments.

---

## 3. Capability Degraded Mode

| Capability | Online Behavior | Offline Behavior |
| :--- | :--- | :--- |
| **Desktop Control** | Full Windows desktop control | 100% operational |
| **Local File System** | Full file search & manipulation | 100% operational |
| **Code Synthesis** | Local or cloud code generation | Local model only (`qwen2.5-coder:7b`) |
| **Knowledge Search** | Hybrid web + local knowledge | Local Knowledge OS & vector store only |
| **Speech STT/TTS** | Cloud or local speech | Local Faster-Whisper & Piper-TTS only |
| **Device Mesh** | WAN / cloud relay | Local Wi-Fi / subnet mesh only |
| **Live Web Research** | Active browser search | **Truthful refusal with local index alternative** |
| **Email / Cloud APIs** | Cloud provider sync | **Honest notification of offline status** |

---

## 4. Truthful Offline Response Interception
When offline, queries targeting live external data trigger truthful fallback explanations:
```
User: "Shivani, what are the latest tech stock earnings today?"
Shivani: "Internet access is currently unavailable, so I cannot perform live web research. I can search your previously indexed local Knowledge OS and documents instead."
```
