"""
SHIVANI Screenshot & Display Capture Tools
Provides registered tools for capturing full-screen, active window,
regional screenshots, and Phase 10 Visual Computer Intelligence.
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from tools.desktop.screen import ScreenCapture
from vision.service import get_vision_service, VisionService


class ScreenshotArgs(BaseModel):
    filename: Optional[str] = Field(default=None, description="Optional custom filename for the screenshot")
    active_window_only: bool = Field(default=False, description="Capture only the currently focused foreground window")
    region: Optional[Dict[str, int]] = Field(default=None, description="Optional bounding box {'left': x, 'top': y, 'width': w, 'height': h}")


class ScreenshotTool(BaseTool):
    name = "computer.screenshot"
    description = "Capture an image of the full desktop, active window, or region for visual observation."
    permission_level = RiskLevel.SAFE
    args_schema = ScreenshotArgs
    timeout = 10.0

    def __init__(self, screen_capture: Optional[ScreenCapture] = None):
        super().__init__()
        self.screen_capture = screen_capture or ScreenCapture()

    async def run(
        self,
        filename: Optional[str] = None,
        active_window_only: bool = False,
        region: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        if active_window_only:
            return await self.screen_capture.capture_active_window(filename=filename)
        return await self.screen_capture.capture(filename=filename, region=region)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        from pathlib import Path
        path = Path(result_data.get("path", ""))
        exists = path.exists() and path.stat().st_size > 0
        return {
            "verified": exists,
            "path": str(path),
            "size_bytes": path.stat().st_size if exists else 0
        }


class VisualInspectArgs(BaseModel):
    monitor_id: Optional[int] = Field(default=None, description="Optional monitor ID to capture and inspect")


class VisualInspectTool(BaseTool):
    name = "computer.visual_inspect"
    description = "Capture screen and run full visual understanding (OCR, UI element detection, layout tree)."
    permission_level = RiskLevel.SAFE
    args_schema = VisualInspectArgs
    timeout = 15.0

    def __init__(self, vision_service: Optional[VisionService] = None):
        super().__init__()
        self.service = vision_service or get_vision_service()

    async def run(self, monitor_id: Optional[int] = None) -> Dict[str, Any]:
        ctx = self.service.capture_and_understand(monitor_id=monitor_id)
        return {
            "screenshot_path": ctx.screenshot_path,
            "element_count": len(ctx.elements),
            "elements": [
                {
                    "id": e.id,
                    "type": e.element_type.value,
                    "text": e.text,
                    "box": e.bounding_box.to_int_dict(),
                    "confidence": round(e.confidence, 3),
                }
                for e in ctx.elements
            ],
            "detected_text": [w.text for w in ctx.ocr.words] if ctx.ocr else [],
            "active_window": ctx.active_window,
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "verified": result_data.get("element_count", 0) >= 0 and "screenshot_path" in result_data,
            "elements_found": result_data.get("element_count", 0),
        }


class VisualFindElementArgs(BaseModel):
    query: str = Field(description="Natural language target query (e.g. 'Submit button', 'input below Username')")


class VisualFindElementTool(BaseTool):
    name = "computer.find_element_by_vision"
    description = "Ground a natural language query or label to an exact UI element and click point using vision."
    permission_level = RiskLevel.SAFE
    args_schema = VisualFindElementArgs
    timeout = 15.0

    def __init__(self, vision_service: Optional[VisionService] = None):
        super().__init__()
        self.service = vision_service or get_vision_service()

    async def run(self, query: str) -> Dict[str, Any]:
        elem, point, conf = self.service.locate_target(query)
        if elem and point:
            return {
                "found": True,
                "target_query": query,
                "element_id": elem.id,
                "element_type": elem.element_type.value,
                "text": elem.text,
                "click_point": point.as_int_tuple(),
                "confidence": round(conf, 3),
                "bounding_box": elem.bounding_box.to_int_dict(),
            }
        return {
            "found": False,
            "target_query": query,
            "details": f"No element matching '{query}' could be grounded on the current screen.",
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "verified": result_data.get("found", False),
            "confidence": result_data.get("confidence", 0.0),
        }


class VisualOCRArgs(BaseModel):
    image_path: Optional[str] = Field(default=None, description="Optional image path to run OCR on (captures screen if omitted)")


class VisualOCRTool(BaseTool):
    name = "computer.ocr_screen"
    description = "Extract all visible text and word coordinates from the screen using OCR."
    permission_level = RiskLevel.SAFE
    args_schema = VisualOCRArgs
    timeout = 15.0

    def __init__(self, vision_service: Optional[VisionService] = None):
        super().__init__()
        self.service = vision_service or get_vision_service()

    async def run(self, image_path: Optional[str] = None) -> Dict[str, Any]:
        if not image_path:
            ctx = self.service.capture_and_understand()
            ocr_res = ctx.ocr
            img_path = ctx.screenshot_path
        else:
            ocr_res = self.service.ocr_engine.extract(image_path)
            img_path = image_path

        return {
            "screenshot_path": img_path,
            "word_count": len(ocr_res.words) if ocr_res else 0,
            "full_text": ocr_res.full_text if ocr_res else "",
            "words": [
                {
                    "text": w.text,
                    "confidence": round(w.confidence, 3),
                    "box": w.bounding_box.to_int_dict(),
                }
                for w in (ocr_res.words if ocr_res else [])
            ],
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "verified": "full_text" in result_data,
            "word_count": result_data.get("word_count", 0),
        }
