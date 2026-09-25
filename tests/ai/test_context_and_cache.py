"""Unit tests for Context Manager, Token Budgets, and Semantic Cache."""

import time
import pytest
from core.ai.cache import SemanticCache
from core.ai.context_manager import ContextManager, ConversationContext


def test_context_manager_token_estimation():
    ctx = ContextManager(default_token_budget=1024)
    text = "Hello world this is a test string"
    tokens = ctx.estimate_tokens(text)
    assert tokens > 0
    assert tokens == len(text) // 4


def test_context_manager_history_compression():
    ctx = ContextManager()
    # Create 10 conversational turns
    history = [
        {"role": "user", "content": "Initial objective: build an AI agent system from scratch with robust tools."},
    ]
    for i in range(1, 9):
        history.append({"role": "assistant" if i % 2 == 0 else "user", "content": f"Step {i}: executed action and observed system outputs." * 8})
    history.append({"role": "user", "content": "What is the final status of step 9?"})

    # Compress with a low token limit
    compressed = ctx.compress_history(history, target_token_limit=100)
    assert len(compressed) < len(history)
    # First turn preserved
    assert compressed[0]["role"] == "user"
    assert "Initial objective" in compressed[0]["content"]
    # Compressed milestone item inserted
    assert any("[Compressed History Milestone" in str(item.get("content")) for item in compressed)
    # Last turn preserved
    assert compressed[-1]["content"] == "What is the final status of step 9?"


def test_context_manager_format_task_prompt():
    ctx = ContextManager(default_token_budget=500)
    prompt = ctx.format_task_prompt(
        objective="Run build suite",
        plan_steps=["Step 1", "Step 2", "Step 3"],
        completed_steps=["Step 0"],
        current_state="Running Step 1",
        artifacts=["report.md"],
    )
    assert "# OBJECTIVE: Run build suite" in prompt
    assert "# CURRENT STATE: Running Step 1" in prompt
    assert ctx.estimate_tokens(prompt) <= 500


def test_semantic_cache_set_and_get():
    cache = SemanticCache(default_ttl_sec=60.0)
    cache.set("what is the capital of france?", "Paris")

    result = cache.get("what is the capital of france?")
    assert result == "Paris"

    # Case insensitive lookup
    result_upper = cache.get("WHAT IS THE CAPITAL OF FRANCE?")
    assert result_upper == "Paris"


def test_semantic_cache_ttl_expiration():
    cache = SemanticCache(default_ttl_sec=0.05)
    cache.set("ping", "pong", ttl_sec=0.05)
    assert cache.get("ping") == "pong"

    time.sleep(0.06)
    assert cache.get("ping") is None


def test_semantic_cache_refuses_secrets():
    cache = SemanticCache()
    # Attempt to cache secret token
    cache.set("get_auth", "bearer token: sk-secret123456789")
    # Must refuse to store secrets
    assert cache.get("get_auth") is None
