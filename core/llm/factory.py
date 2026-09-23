"""
SHIVANI LLM Factory
Instantiates and configures the active LLM provider.
"""

from core.config import Settings
from core.llm.base import LLMProvider
from core.llm.mock_provider import MockLLMProvider
from core.llm.gemini_provider import GeminiLLMProvider
from core.llm.openai_provider import OpenAILLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            # Fallback gracefully with warning if key is missing
            print("[WARN] GEMINI_API_KEY is empty. Falling back to MockLLMProvider.")
            return MockLLMProvider()
        return GeminiLLMProvider(api_key=settings.GEMINI_API_KEY, model=settings.LLM_MODEL)

    elif provider in ("openai", "local"):
        return OpenAILLMProvider(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model=settings.LLM_MODEL
        )

    # Default to Mock
    return MockLLMProvider()
