"""
SHIVANI Native Ollama Provider (Offline & Local AI)
Enables 100% offline, local execution with local open-weights LLMs (Llama 3, Qwen 2.5, DeepSeek, Mistral).
"""

import json
import time
from typing import Any, Dict, List, Optional, Type
import httpx
from pydantic import BaseModel

from core.providers.base import LLMProvider
from core.tasks.task import TaskPlan
from core.errors import ProviderError, ValidationError


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "llama3:latest",
        timeout: float = 60.0
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        url = f"{self.base_url}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                message_content = data.get("message", {}).get("content", "")
                return message_content.strip()
        except httpx.ConnectError:
            raise ProviderError(
                f"Cannot connect to local Ollama server at {self.base_url}. Ensure Ollama is installed and running (`ollama serve`).",
                recovery_suggestion="Run 'ollama serve' in a terminal or switch LLM_PROVIDER to gemini or openai."
            )
        except Exception as e:
            raise ProviderError(f"Ollama request error: {e}")

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        augmented_prompt = f"{prompt}\n\nRespond ONLY with valid JSON conforming to this schema:\n{schema_json}"
        raw_text = await self.generate(augmented_prompt, system_prompt=system_prompt, temperature=0.1)

        clean = raw_text.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]

        try:
            return schema.model_validate(json.loads(clean.strip()))
        except Exception as e:
            raise ValidationError(f"Ollama schema validation failed: {e}")

    async def generate_plan(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        tools_str = json.dumps(available_tools, indent=2)
        ctx_str = json.dumps(context or {}, indent=2)
        prompt = f"""You are SHIVANI, an autonomous AI computer agent.
Principle: OBSERVE -> PLAN -> ACT -> VERIFY.
Create a structured task plan in JSON format.

Available Tools:
{tools_str}

Context:
{ctx_str}

User Query:
{user_query}
"""
        system = "Respond ONLY with a valid JSON matching the TaskPlan schema."
        return await self.generate_structured(prompt, TaskPlan, system_prompt=system)

    async def health_check(self) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    latency = (time.perf_counter() - start) * 1000.0
                    models_data = resp.json().get("models", [])
                    available_models = [m.get("name") for m in models_data]
                    return {
                        "healthy": True,
                        "provider": "ollama",
                        "model": self.model,
                        "latency_ms": round(latency, 2),
                        "available_models": available_models,
                    }
                return {
                    "healthy": False,
                    "provider": "ollama",
                    "error": f"Ollama HTTP {resp.status_code}"
                }
        except Exception as e:
            return {
                "healthy": False,
                "provider": "ollama",
                "error": f"Ollama unavailable: {e}"
            }
