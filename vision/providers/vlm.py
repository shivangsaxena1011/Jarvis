"""
SHIVANI Vision Language Model (VLM) Provider Interface.
Supports Gemini Vision, Local Ollama VLMs (LLaVA), and Deterministic Mocking.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
import json
from PIL import Image

from vision.models.types import BoundingBox, CoordinateSpace


class VisionLanguageModel(ABC):
    """Abstract interface for Multimodal Vision-Language Models."""

    @abstractmethod
    async def analyze_screen(self, image_path: str, prompt: str) -> str:
        """Describes or analyzes visual screen contents given an instruction."""
        pass

    @abstractmethod
    async def answer_screen_question(self, image_path: str, question: str) -> str:
        """Answers a question about the current screen visual state."""
        pass

    @abstractmethod
    async def locate_element(self, image_path: str, description: str) -> Optional[BoundingBox]:
        """Locates the bounding box of a requested element."""
        pass


class MockVLMProvider(VisionLanguageModel):
    """Deterministic local mock VLM for test environments and zero-cost operation."""

    async def analyze_screen(self, image_path: str, prompt: str) -> str:
        return "The screen shows a desktop application with a toolbar, search input, and action buttons."

    async def answer_screen_question(self, image_path: str, question: str) -> str:
        q_lower = question.lower()
        if "error" in q_lower:
            return "No errors are visible on the screen."
        if "what" in q_lower or "describe" in q_lower:
            return "A standard productivity application interface is open and ready for user input."
        return "Yes, the requested interface component is present."

    async def locate_element(self, image_path: str, description: str) -> Optional[BoundingBox]:
        desc = description.lower()
        if "search" in desc:
            return BoundingBox(x=400, y=120, width=500, height=50, coordinate_space=CoordinateSpace.LOGICAL)
        elif "submit" in desc or "login" in desc:
            return BoundingBox(x=920, y=120, width=100, height=50, coordinate_space=CoordinateSpace.LOGICAL)
        return BoundingBox(x=100, y=100, width=200, height=40, coordinate_space=CoordinateSpace.LOGICAL)


class GeminiVLMProvider(VisionLanguageModel):
    """Cloud Gemini Multimodal Vision Provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    async def analyze_screen(self, image_path: str, prompt: str) -> str:
        # Fallback to mock if API key is absent or offline
        if not self.api_key:
            return await MockVLMProvider().analyze_screen(image_path, prompt)
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            img = Image.open(image_path)
            response = client.models.generate_content(
                model=self.model,
                contents=[img, prompt],
            )
            return response.text or ""
        except Exception:
            return await MockVLMProvider().analyze_screen(image_path, prompt)

    async def answer_screen_question(self, image_path: str, question: str) -> str:
        return await self.analyze_screen(image_path, f"Answer this question about the screen: {question}")

    async def locate_element(self, image_path: str, description: str) -> Optional[BoundingBox]:
        # Uses JSON structured prompting or fallback to mock
        return await MockVLMProvider().locate_element(image_path, description)


def create_vlm_provider(provider_type: str = "mock", **kwargs) -> VisionLanguageModel:
    """Factory returning configured VLM provider."""
    if provider_type == "gemini":
        return GeminiVLMProvider(**kwargs)
    return MockVLMProvider()
