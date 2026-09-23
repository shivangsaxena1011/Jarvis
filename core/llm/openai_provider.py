"""
SHIVANI OpenAI Compatible LLM Provider
Supports OpenAI and local compatible endpoints (e.g. vLLM, Ollama, LM Studio).
"""

import json
from typing import Any, Dict, List, Optional
import httpx
from core.llm.base import LLMProvider, TaskPlan


class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        self.api_key = api_key or "local"
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate_text(
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

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    async def generate_plan(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        tools_desc = json.dumps(available_tools, indent=2)
        ctx_desc = json.dumps(context or {}, indent=2)

        prompt = f"""You are SHIVANI, an autonomous AI computer agent.
Principle: OBSERVE -> PLAN -> ACT -> VERIFY.
Create a structured task plan in JSON format.

Available Tools:
{tools_desc}

Context:
{ctx_desc}

User Query:
{user_query}
"""
        system = "You are a planning engine. Always respond with valid JSON matching TaskPlan schema."
        text = await self.generate_text(prompt, system_prompt=system, temperature=0.1)

        try:
            clean_text = text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            data = json.loads(clean_text.strip())
            return TaskPlan(**data)
        except Exception as e:
            return TaskPlan(
                goal=user_query,
                rationale=f"Fallback plan due to parsing error: {e}",
                steps=[]
            )
