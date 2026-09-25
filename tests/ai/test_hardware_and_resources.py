"""Unit tests for Hardware Profiling and Model Resource Management."""

import pytest
from core.ai.hardware import detect_hardware, HardwareProfiler
from core.ai.local_runtime import MockLocalRuntime
from core.ai.resource_manager import ModelResourceManager


def test_hardware_profiler_detection():
    profiler = HardwareProfiler()
    profile = profiler.detect()

    assert profile.cpu_cores > 0
    assert profile.ram_total_gb > 0.0
    assert profile.ram_available_gb > 0.0
    assert profile.gpu_vendor in ["NVIDIA", "AMD", "Intel", "Apple", "None"]
    assert profile.os_platform in ["Windows", "Linux", "Darwin"]
    assert profile.to_dict()["cpu_cores"] == profile.cpu_cores


def test_resource_manager_warming_and_eviction():
    mock_rt = MockLocalRuntime(available=True)
    res_mgr = ModelResourceManager(local_runtime=mock_rt, max_concurrent_models=1)

    # Warm model A
    assert res_mgr.warm_model("llama3.1:8b") is True
    assert "llama3.1:8b" in res_mgr._warmed_models
    assert "llama3.1:8b" in mock_rt.warmed_models

    # Acquire execution slot for model B -> should evict model A since max_concurrent=1
    assert res_mgr.acquire_execution_slot("phi3:mini") is True
    assert res_mgr._active_model_id == "phi3:mini"
    assert "llama3.1:8b" not in mock_rt.warmed_models

    # Release slot
    res_mgr.release_execution_slot("phi3:mini")
    assert res_mgr._active_inference_count == 0

    # Unload model explicitly
    assert res_mgr.unload_model("phi3:mini") is True


def test_resource_status_reporting():
    mock_rt = MockLocalRuntime(available=True)
    res_mgr = ModelResourceManager(local_runtime=mock_rt)
    status = res_mgr.get_resource_status()

    assert "ram_used_percent" in status
    assert "ram_available_gb" in status
    assert "gpu_vendor" in status
    assert "active_inferences" in status
