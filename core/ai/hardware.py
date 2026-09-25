"""Hardware Detection and System Resource Profiler for Phase 19.

Inspects host CPU, RAM, GPU vendors (NVIDIA, AMD, Intel, None), VRAM, and storage
to provide empirical local model capacity recommendations without assuming CUDA.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from typing import Optional

import psutil

from core.ai.models import HardwareProfile

logger = logging.getLogger("shivani.ai.hardware")


def detect_hardware() -> HardwareProfile:
    """Detect available hardware capabilities on host system."""
    # 1. CPU & Operating System
    cpu_cores = os.cpu_count() or 4
    cpu_model = platform.processor() or "Generic CPU"
    os_name = platform.system()

    # 2. System RAM
    vm = psutil.virtual_memory()
    ram_total_gb = vm.total / (1024 ** 3)
    ram_available_gb = vm.available / (1024 ** 3)

    # 3. Storage
    disk = shutil.disk_usage(".")
    storage_free_gb = disk.free / (1024 ** 3)

    # 4. GPU & VRAM Detection
    gpu_vendor = "None"
    gpu_model = "Integrated Graphics"
    vram_total_gb = 0.0
    vram_available_gb = 0.0
    has_cuda = False

    # A. Check NVIDIA via nvidia-smi
    try:
        smi_out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2.0,
        )
        if smi_out.strip():
            parts = [p.strip() for p in smi_out.strip().split("\n")[0].split(",")]
            if len(parts) >= 3:
                gpu_vendor = "NVIDIA"
                gpu_model = parts[0]
                vram_total_gb = float(parts[1]) / 1024.0
                vram_available_gb = float(parts[2]) / 1024.0
                has_cuda = True
    except Exception:
        pass

    # B. If not NVIDIA, inspect Windows WMI / CimInstance for AMD or Intel GPUs
    if gpu_vendor == "None" and os_name == "Windows":
        try:
            cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"]
            res = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=3.0)
            names = [n.strip() for n in res.splitlines() if n.strip()]
            for name in names:
                n_lower = name.lower()
                if "amd" in n_lower or "radeon" in n_lower:
                    gpu_vendor = "AMD"
                    gpu_model = name
                    break
                elif "intel" in n_lower:
                    gpu_vendor = "Intel"
                    gpu_model = name
                elif "nvidia" in n_lower:
                    gpu_vendor = "NVIDIA"
                    gpu_model = name
        except Exception:
            pass

    # 5. Compute recommended local model size
    rec_size = "None"
    if vram_total_gb >= 24.0 or ram_total_gb >= 64.0:
        rec_size = "32B"
    elif vram_total_gb >= 12.0 or ram_total_gb >= 32.0:
        rec_size = "14B"
    elif vram_total_gb >= 8.0 or ram_total_gb >= 16.0:
        rec_size = "8B"
    elif vram_total_gb >= 4.0 or ram_total_gb >= 8.0:
        rec_size = "3B"

    profile = HardwareProfile(
        cpu_cores=cpu_cores,
        cpu_model=cpu_model,
        ram_total_gb=ram_total_gb,
        ram_available_gb=ram_available_gb,
        gpu_vendor=gpu_vendor,
        gpu_model=gpu_model,
        vram_total_gb=vram_total_gb,
        vram_available_gb=vram_available_gb,
        storage_free_gb=storage_free_gb,
        os_platform=os_name,
        has_cuda=has_cuda,
        recommended_local_size=rec_size,
    )

    logger.info(
        f"Detected Hardware: {gpu_vendor} GPU ({gpu_model}), {ram_total_gb:.1f}GB RAM, "
        f"{vram_total_gb:.1f}GB VRAM -> Recommended Local Size: {rec_size}"
    )
    return profile


class HardwareProfiler:
    """Convenience class to profile hardware and cache results."""

    def __init__(self):
        self._cached: Optional[HardwareProfile] = None

    def detect(self, force_refresh: bool = False) -> HardwareProfile:
        if self._cached is None or force_refresh:
            self._cached = detect_hardware()
        return self._cached

