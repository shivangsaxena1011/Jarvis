"""
SHIVANI Provider Factory
Instantiates and configures the active LLM provider.
"""

from core.config import Settings
from core.providers.base import LLMProvider
from core.providers.mock import MockProvider
from core.providers.gemini import GeminiProvider
from core.providers.openai import OpenAICompatibleProvider
from core.providers.ollama import OllamaProvider
from core.providers.fallback import FallbackProviderChain


def create_provider(settings: Settings) -> LLMProvider:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            print("[WARN] GEMINI_API_KEY is empty. Falling back to MockProvider.")
            return MockProvider()
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.LLM_MODEL)

    elif provider in ("openai", "local"):
        return OpenAICompatibleProvider(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model=settings.LLM_MODEL
        )

    elif provider == "ollama":
        base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        return OllamaProvider(
            base_url=base_url,
            model=settings.LLM_MODEL
        )

    elif provider in ("fallback", "chain"):
        chain = []
        if settings.GEMINI_API_KEY:
            chain.append(GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.LLM_MODEL))
        if settings.OPENAI_API_KEY:
            chain.append(OpenAICompatibleProvider(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL, model=settings.LLM_MODEL))
        chain.append(OllamaProvider(model=settings.LLM_MODEL))
        chain.append(MockProvider())
        return FallbackProviderChain(chain)

    # Default Mock
    return MockProvider()

