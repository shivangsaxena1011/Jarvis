"""
SHIVANI Google Gemini LLM Provider
Interacts with the Google Gemini API directly using HTTPX.
"""

import json
from typing import Any, Dict, List, Optional
import httpx
from core.llm.base import LLMProvider, TaskPlan


class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except (KeyError, IndexError):
                return ""

    async def generate_plan(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        tools_desc = json.dumps(available_tools, indent=2)
        ctx_desc = json.dumps(context or {}, indent=2)

        prompt = f"""You are SHIVANI, an autonomous AI computer agent.
Your core principle is: OBSERVE -> PLAN -> ACT -> VERIFY.
Break down the user query into a structured execution plan.

Available Tools:
{tools_desc}

Current Context:
{ctx_desc}

User Query:
{user_query}

Respond ONLY with a valid JSON object matching this schema:
{{
  "goal": "summary of user goal",
  "rationale": "explanation of execution approach",
  "steps": [
    {{
      "id": "1",
      "tool": "tool.name",
      "action": "description of step",
      "arguments": {{"param": "val"}},
      "requires_confirmation": false,
      "expected_outcome": "what to verify after execution"
    }}
  ]
}}
"""
        text = await self.generate_text(prompt, temperature=0.1)
        # Parse JSON from response
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
            # Fallback plan if JSON parsing fails
            return TaskPlan(
                goal=user_query,
                rationale=f"Fallback plan due to parsing error: {e}",
                steps=[]
            )
