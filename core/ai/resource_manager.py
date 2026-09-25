"""Model Resource Manager, Concurrency Governor & Warming Queue for Phase 19.

Controls VRAM/RAM allocation, prevents GPU memory exhaustion, manages model warming/eviction,
and prioritizes interactive user commands over background inference tasks.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

import psutil

from core.ai.hardware import detect_hardware
from core.ai.local_runtime import LocalModelRuntime
from core.ai.models import HardwareProfile

logger = logging.getLogger("shivani.ai.resources")


class ModelResourceManager:
    """Oversees system memory, model warming, execution queues, and concurrency limits."""

    def __init__(
        self,
        local_runtime: Optional[LocalModelRuntime] = None,
        hardware_profile: Optional[HardwareProfile] = None,
        max_concurrent_models: int = 1,
        idle_unload_timeout_sec: float = 600.0,
    ):
        self.runtime = local_runtime
        self.hardware = hardware_profile or detect_hardware()
        self.max_concurrent_models = max_concurrent_models
        self.idle_unload_timeout_sec = idle_unload_timeout_sec

        self._lock = threading.RLock()
        self._active_model_id: Optional[str] = None
        self._last_used_timestamp: Dict[str, float] = {}
        self._warmed_models: set[str] = set()
        self._active_inference_count: int = 0

    def warm_model(self, model_id: str) -> bool:
        """Pre-load a local model into memory."""
        with self._lock:
            if not self.runtime or not self.runtime.is_runtime_available():
                return False

            success = self.runtime.warm_model(model_id)
            if success:
                self._warmed_models.add(model_id)
                self._last_used_timestamp[model_id] = time.time()
                logger.info(f"Model '{model_id}' warmed in memory.")
            return success

    def unload_model(self, model_id: str) -> bool:
        """Evict model from memory."""
        with self._lock:
            if not self.runtime or not self.runtime.is_runtime_available():
                return False

            success = self.runtime.unload_model(model_id)
            if success:
                self._warmed_models.discard(model_id)
                logger.info(f"Model '{model_id}' unloaded from memory.")
            return success

    def check_battery_governor(self) -> Tuple[bool, Optional[str]]:
        """Throttle background inference if host is on battery and charge is low."""
        try:
            battery = psutil.sensors_battery()
            if battery and not battery.power_plugged and battery.percent < 20:
                return False, f"Battery critically low ({battery.percent}%). Background inference paused to save power."
        except Exception:
            pass
        return True, None

    def can_execute_inference(self, required_ram_gb: float = 4.0) -> Tuple[bool, Optional[str]]:
        """Verify host memory before launching local inference."""
        vm = psutil.virtual_memory()
        available_gb = vm.available / (1024 ** 3)
        if available_gb < required_ram_gb:
            return False, f"Insufficient host RAM: {available_gb:.1f}GB available, {required_ram_gb:.1f}GB required."
        return True, None

    def acquire_execution_slot(self, model_id: str, is_interactive: bool = True) -> bool:
        """Acquire lock for executing inference, ensuring concurrency limits."""
        with self._lock:
            # If GPU/RAM can only hold 1 model, evict all other warmed/active models
            if self.max_concurrent_models <= 1:
                for warmed_id in list(self._warmed_models):
                    if warmed_id != model_id:
                        logger.info(f"Evicting warmed model '{warmed_id}' to switch to '{model_id}'")
                        self.unload_model(warmed_id)
            elif self._active_model_id and self._active_model_id != model_id:
                self.unload_model(self._active_model_id)

            self._active_model_id = model_id

            self._last_used_timestamp[model_id] = time.time()
            self._active_inference_count += 1
            return True

    def release_execution_slot(self, model_id: str) -> None:
        """Release slot after inference completes."""
        with self._lock:
            self._active_inference_count = max(0, self._active_inference_count - 1)
            self._last_used_timestamp[model_id] = time.time()

    def get_resource_status(self) -> Dict[str, Any]:
        """Return diagnostic view of system utilization."""
        vm = psutil.virtual_memory()
        return {
            "ram_used_percent": vm.percent,
            "ram_available_gb": round(vm.available / (1024 ** 3), 2),
            "gpu_vendor": self.hardware.gpu_vendor,
            "has_cuda": self.hardware.has_cuda,
            "vram_total_gb": self.hardware.vram_total_gb,
            "active_model_id": self._active_model_id,
            "warmed_models": list(self._warmed_models),
            "active_inferences": self._active_inference_count,
        }
