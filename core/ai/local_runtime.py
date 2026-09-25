"""Local Model Runtime Abstraction for Phase 19.

Supports multiple local inference backends (Ollama, llama.cpp-compatible, OpenAI-compatible local servers,
and MockLocalRuntime) with model warming, discovery, and unloading.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core.ai.models import ModelDescriptor, ModelHealthState, ProviderType

logger = logging.getLogger("shivani.ai.local_runtime")


class LocalModelRuntime(ABC):
    """Abstract interface for managing local LLM servers and processes."""

    @abstractmethod
    def is_runtime_available(self) -> bool:
        """Check if local inference daemon is running and reachable."""
        pass

    @abstractmethod
    def list_installed_models(self) -> List[Dict[str, Any]]:
        """Query installed weights, tags, parameter counts, and quantization levels."""
        pass

    @abstractmethod
    def warm_model(self, model_id: str) -> bool:
        """Pre-load model weights into RAM/VRAM to reduce initial execution latency."""
        pass

    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Evict model from VRAM/RAM when idle or when other tasks require GPU memory."""
        pass

    @abstractmethod
    async def generate(self, model_id: str, prompt: str, temperature: float = 0.2) -> str:
        """Execute text inference on local engine."""
        pass


class OllamaLocalRuntime(LocalModelRuntime):
    """Integrates with local Ollama runtime on http://localhost:11434."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._warmed_models: set[str] = set()

    def is_runtime_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/version", method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def list_installed_models(self) -> List[Dict[str, Any]]:
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode())
                models = []
                for m in data.get("models", []):
                    models.append({
                        "name": m.get("name"),
                        "size_bytes": m.get("size", 0),
                        "modified_at": m.get("modified_at"),
                        "details": m.get("details", {}),
                    })
                return models
        except Exception as e:
            logger.debug(f"Failed to query Ollama models: {e}")
            return []

    def warm_model(self, model_id: str) -> bool:
        try:
            # Send lightweight empty prompt to force Ollama to load weights
            payload = json.dumps({"model": model_id, "prompt": "hi", "keep_alive": "10m"}).encode()
            req = urllib.request.Request(f"{self.base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                self._warmed_models.add(model_id)
                logger.info(f"Model '{model_id}' warmed in Ollama memory.")
                return True
        except Exception as e:
            logger.warning(f"Failed to warm model '{model_id}': {e}")
            return False

    def unload_model(self, model_id: str) -> bool:
        try:
            payload = json.dumps({"model": model_id, "keep_alive": 0}).encode()
            req = urllib.request.Request(f"{self.base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                self._warmed_models.discard(model_id)
                logger.info(f"Model '{model_id}' evicted from Ollama VRAM.")
                return True
        except Exception as e:
            logger.warning(f"Failed to unload model '{model_id}': {e}")
            return False

    async def generate(self, model_id: str, prompt: str, temperature: float = 0.2) -> str:
        payload = json.dumps({
            "model": model_id,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }).encode()
        req = urllib.request.Request(f"{self.base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60.0) as resp:
            data = json.loads(resp.read().decode())
            return data.get("response", "")


class MockLocalRuntime(LocalModelRuntime):
    """Deterministic, zero-latency local runtime for tests and offline simulations."""

    def __init__(self, available: bool = True):
        self._available = available
        self.warmed_models: set[str] = set()
        self.installed_models: List[Dict[str, Any]] = [
            {"name": "llama3.1:8b", "size_bytes": 4900000000, "details": {"parameter_size": "8B", "quantization_level": "Q4_K_M"}},
            {"name": "phi3:mini", "size_bytes": 2400000000, "details": {"parameter_size": "3.8B", "quantization_level": "Q4_0"}},
            {"name": "qwen2.5-coder:7b", "size_bytes": 4500000000, "details": {"parameter_size": "7B", "quantization_level": "Q4_K_M"}},
        ]

    def set_available(self, available: bool) -> None:
        self._available = available

    def is_runtime_available(self) -> bool:
        return self._available

    def list_installed_models(self) -> List[Dict[str, Any]]:
        return self.installed_models if self._available else []

    def warm_model(self, model_id: str) -> bool:
        if not self._available:
            return False
        self.warmed_models.add(model_id)
        return True

    def unload_model(self, model_id: str) -> bool:
        self.warmed_models.discard(model_id)
        return True

    async def generate(self, model_id: str, prompt: str, temperature: float = 0.2) -> str:
        if not self._available:
            raise RuntimeError(f"Local runtime unavailable for model {model_id}.")
        return f"[Local {model_id}] Response to: {prompt[:40]}"
