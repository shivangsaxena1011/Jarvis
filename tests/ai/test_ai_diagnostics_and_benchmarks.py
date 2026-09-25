"""Unit tests for AI Doctor diagnostics and Model Benchmark Suite."""

import pytest
from core.ai.benchmark import ModelBenchmarkSuite
from core.ai.doctor import AIDoctor
from core.ai.local_runtime import MockLocalRuntime
from core.ai.offline import OfflineManager
from core.ai.registry import ModelRegistry


@pytest.fixture
def mock_runtime():
    return MockLocalRuntime(available=True)


@pytest.fixture
def doctor(mock_runtime):
    reg = ModelRegistry()
    offline = OfflineManager()
    return AIDoctor(registry=reg, local_runtime=mock_runtime, offline_manager=offline)


def test_doctor_run_diagnostics(doctor):
    diag = doctor.run_diagnostics()
    assert "overall_status" in diag
    assert "checks" in diag
    assert "hardware" in diag["checks"]
    assert "local_runtime" in diag["checks"]
    assert "cloud_providers" in diag["checks"]
    assert "offline_readiness" in diag["checks"]
    assert isinstance(diag["recommendations"], list)


def test_doctor_format_report(doctor):
    report = doctor.format_report()
    assert "SHIVANI AI DOCTOR DIAGNOSTIC REPORT" in report
    assert "HARDWARE & ACCELERATION:" in report
    assert "LOCAL RUNTIME & MODELS:" in report
    assert "OFFLINE READINESS:" in report


@pytest.mark.asyncio
async def test_benchmark_suite_run_benchmark(mock_runtime):
    suite = ModelBenchmarkSuite(default_runtime=mock_runtime)
    res = await suite.run_benchmark(model_id="phi3:mini")

    assert res.model_id == "phi3:mini"
    assert res.tokens_per_second > 0.0
    assert res.latency_first_token_ms >= 0.0
    assert res.tool_calling_passed is True
    assert res.structured_output_passed is True
    assert res.memory_used_mb > 0.0

    # Ensure cached
    cached = suite.get_result("phi3:mini")
    assert cached is not None
    assert cached.model_id == "phi3:mini"


@pytest.mark.asyncio
async def test_benchmark_suite_run_all(mock_runtime):
    suite = ModelBenchmarkSuite(default_runtime=mock_runtime)
    models = ["llama3.1:8b", "phi3:mini"]
    results = await suite.run_all(model_ids=models)

    assert len(results) == 2
    cached_all = suite.get_cached_results()
    assert len(cached_all) >= 2
