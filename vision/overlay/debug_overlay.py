"""
SHIVANI Visual Debug Overlay Engine.
Draws color-coded bounding boxes, labels, and confidence overlays on screenshots.
"""

from typing import List, Tuple, Union, Optional
from PIL import Image, ImageDraw, ImageFont

from vision.models.types import VisualElementType, BoundingBox
from vision.models.schemas import UIElement

# Color mapping by element type
ELEMENT_COLORS = {
    VisualElementType.BUTTON: (40, 200, 60),      # Bright Green
    VisualElementType.INPUT: (50, 130, 240),      # Bright Blue
    VisualElementType.TEXT: (240, 200, 40),       # Warm Yellow
    VisualElementType.CHECKBOX: (200, 100, 240),  # Purple
    VisualElementType.MODAL: (240, 60, 60),       # Red
    VisualElementType.CARD: (180, 180, 180),      # Grey
    VisualElementType.CONTAINER: (100, 100, 100), # Dark Grey
    VisualElementType.UNKNOWN: (0, 255, 255),     # Cyan
}


class VisualDebugOverlay:
    """Renders visual bounding box debug annotations on screenshots."""

    def render_overlay(
        self,
        image: Union[str, Image.Image],
        elements: List[UIElement],
        save_path: Optional[str] = None,
    ) -> Tuple[str, Image.Image]:
        """
        Draws bounding box outlines and text tags onto the screenshot.
        """
        pil_img = Image.open(image) if isinstance(image, str) else image.copy()
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        draw = ImageDraw.Draw(pil_img)

        for elem in elements:
            box = elem.bounding_box
            color = ELEMENT_COLORS.get(elem.element_type, (0, 255, 255))

            x0 = int(round(box.left))
            y0 = int(round(box.top))
            x1 = int(round(box.right))
            y1 = int(round(box.bottom))

            # Draw rectangle boundary (width=2)
            draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

            # Draw label tag
            tag_label = f"{elem.element_type.value}: {elem.text[:15] if elem.text else ''} ({int(elem.confidence*100)}%)"
            draw.text((x0 + 2, max(0, y0 - 12)), tag_label, fill=color)

        if not save_path:
            import tempfile, time, os
            save_path = os.path.join(tempfile.gettempdir(), f"shivani_overlay_{int(time.time()*1000)}.png")

        pil_img.save(save_path, format="PNG")
        return (save_path, pil_img)
