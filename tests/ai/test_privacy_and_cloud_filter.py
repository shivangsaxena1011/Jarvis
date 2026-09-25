"""Unit tests for Privacy Classification, Secret Redaction, and Cloud Filter."""

import pytest
from core.ai.models import PrivacyLevel, ProviderType
from core.ai.privacy import CloudContextFilter, DataClassifier
from core.ai.registry import ModelRegistry
from core.ai.router import ModelRouter


def test_classify_api_token_critical():
    prompt = "Here is my key: api_key='sk-1234567890abcdef1234567890abcdef', help me test it."
    level, reasons = DataClassifier.classify(prompt)
    assert level == PrivacyLevel.CRITICAL
    assert any("secret" in r.lower() or "token" in r.lower() for r in reasons)


def test_classify_credit_card_critical():
    prompt = "Charge card 4111-2222-3333-4444 for subscription renewal"
    level, reasons = DataClassifier.classify(prompt)
    assert level == PrivacyLevel.CRITICAL


def test_classify_metadata_dotenv_file():
    prompt = "Read configuration values from this file"
    level, reasons = DataClassifier.classify(prompt, metadata={"file_path": "C:/Project/.env"})
    assert level == PrivacyLevel.CRITICAL
    assert any(".env" in r for r in reasons)


def test_classify_sensitive_financial_terms():
    prompt = "Analyze my tax return and annual salary breakdown for 2025"
    level, reasons = DataClassifier.classify(prompt)
    assert level == PrivacyLevel.SENSITIVE


def test_cloud_context_filter_blocks_critical():
    with pytest.raises(PermissionError, match="Critical secret data detected"):
        CloudContextFilter.sanitize_for_cloud(
            text="Private token: sk-abcdef1234567890abcdef1234567890",
            privacy_level=PrivacyLevel.CRITICAL,
            allow_cloud=True,
        )


def test_cloud_context_filter_redacts_tokens():
    text = "The service returned an error with bearer token: bearer 9876543210fedcba"
    sanitized, was_redacted = CloudContextFilter.sanitize_for_cloud(
        text=text,
        privacy_level=PrivacyLevel.LOW_SENSITIVITY,
        allow_cloud=True,
    )
    assert was_redacted is True
    assert "***REDACTED_SECRET***" in sanitized


def test_router_enforces_local_for_critical_prompt():
    reg = ModelRegistry()
    router = ModelRouter(registry=reg)

    prompt = "My password is password='SuperSecretPassword123!', how to hash this in python?"
    decision = router.route(prompt)

    # Must be routed to local provider, never cloud
    assert decision.privacy_level == PrivacyLevel.CRITICAL
    assert decision.provider_type == ProviderType.LOCAL
    assert decision.constraints["allow_cloud"] is False
