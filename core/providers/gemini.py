"""
SHIVANI Google Gemini Provider
Direct asynchronous REST interface for Google Gemini API models.
"""

import json
import time
from typing import Any, Dict, List, Optional, Type
import httpx
from pydantic import BaseModel
from core.providers.base import LLMProvider
from core.tasks.task import TaskPlan
from core.errors import ProviderError, ValidationError


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        if not self.api_key:
            raise ProviderError("GEMINI_API_KEY is not configured.")

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature}
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            raise ProviderError(f"Gemini API request failed: {e}")

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        augmented_prompt = f"{prompt}\n\nYou MUST respond with ONLY a valid JSON object matching this JSON Schema:\n{schema_json}"
        raw_text = await self.generate(augmented_prompt, system_prompt=system_prompt, temperature=0.1)

        # Clean JSON markdown blocks
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        try:
            data = json.loads(clean_text.strip())
            return schema.model_validate(data)
        except Exception as e:
            raise ValidationError(f"Failed to validate model response against schema {schema.__name__}: {e}")

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
        system = "Respond ONLY with a valid JSON matching the TaskPlan schema with fields: goal, rationale, steps."
        return await self.generate_structured(prompt, TaskPlan, system_prompt=system)

    async def health_check(self) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "healthy": False,
                "provider": "gemini",
                "model": self.model,
                "error": "GEMINI_API_KEY is not set."
            }

        start = time.perf_counter()
        try:
            # Lightweight ping
            await self.generate("ping", temperature=0.0)
            latency = (time.perf_counter() - start) * 1000.0
            return {
                "healthy": True,
                "provider": "gemini",
                "model": self.model,
                "latency_ms": round(latency, 2)
            }
        except Exception as e:
            return {
                "healthy": False,
                "provider": "gemini",
                "model": self.model,
                "error": str(e)
            }
