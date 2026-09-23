"""
SHIVANI OpenAI Compatible Provider
Async client for OpenAI and local compatible endpoints (e.g. vLLM, Ollama, LM Studio).
"""

import json
import time
from typing import Any, Dict, List, Optional, Type
import httpx
from pydantic import BaseModel
from core.providers.base import LLMProvider
from core.tasks.task import TaskPlan
from core.errors import ProviderError, ValidationError


class OpenAICompatibleProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        self.api_key = api_key or "local"
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise ProviderError(f"OpenAI API request failed: {e}")

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
            raise ValidationError(f"Schema validation failed: {e}")

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
        if not self.api_key and "api.openai.com" in self.base_url:
            return {
                "healthy": False,
                "provider": "openai",
                "model": self.model,
                "error": "OPENAI_API_KEY is not set."
            }

        start = time.perf_counter()
        try:
            await self.generate("ping", temperature=0.0)
            latency = (time.perf_counter() - start) * 1000.0
            return {
                "healthy": True,
                "provider": "openai",
                "model": self.model,
                "latency_ms": round(latency, 2)
            }
        except Exception as e:
            return {
                "healthy": False,
                "provider": "openai",
                "model": self.model,
                "error": str(e)
            }
