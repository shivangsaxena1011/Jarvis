"""
SHIVANI High-DPI Multi-Monitor Screen Capture Engine.
Supports ultra-fast multi-monitor captures with mss, PIL, or PyAutoGUI.
"""

from typing import Optional, Tuple
import os
import time
import tempfile
from PIL import Image

from vision.models.types import (
    BoundingBox,
    CoordinateSpace,
    MonitorInfo,
    Point,
    Size,
)
from vision.capture.monitors import enumerate_monitors, get_primary_monitor
from vision.capture.coordinates import CoordinateTransformer


class ScreenCaptureEngine:
    """High-performance capture engine with multi-monitor and high-DPI awareness."""

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        os.makedirs(self.temp_dir, exist_ok=True)

    def capture_full_screen(
        self,
        monitor_id: Optional[int] = None,
        save_path: Optional[str] = None,
    ) -> Tuple[str, MonitorInfo, Image.Image]:
        """
        Captures the entire screen of a target monitor (or primary).
        Returns:
            Tuple of (saved_file_path, monitor_info, PIL Image)
        """
        monitors = enumerate_monitors()
        target_monitor: MonitorInfo = get_primary_monitor()

        if monitor_id is not None:
            for m in monitors:
                if m.id == monitor_id:
                    target_monitor = m
                    break

        img: Optional[Image.Image] = None

        # Method 1: mss (ultra fast, multi-monitor aware)
        try:
            import mss
            sct_cls = getattr(mss, "MSS", getattr(mss, "mss", None))
            with sct_cls() as sct:
                # mss monitors: index 0 is all monitors combined, 1 is primary, 2+ are secondaries
                # Match by coordinate bounding box
                monitor_dict = {
                    "top": int(target_monitor.y),
                    "left": int(target_monitor.x),
                    "width": int(target_monitor.width),
                    "height": int(target_monitor.height),
                }
                sct_img = sct.grab(monitor_dict)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        except Exception:
            pass

        # Method 2: PIL ImageGrab
        if img is None:
            try:
                from PIL import ImageGrab
                bbox = (
                    target_monitor.x,
                    target_monitor.y,
                    target_monitor.x + target_monitor.width,
                    target_monitor.y + target_monitor.height,
                )
                img = ImageGrab.grab(bbox=bbox)
            except Exception:
                pass

        # Method 3: PyAutoGUI
        if img is None:
            try:
                import pyautogui
                img = pyautogui.screenshot(
                    region=(
                        target_monitor.x,
                        target_monitor.y,
                        target_monitor.width,
                        target_monitor.height,
                    )
                )
            except Exception:
                # Synthetic fallback for headless testing
                img = Image.new("RGB", (target_monitor.width, target_monitor.height), color=(240, 240, 240))

        # Output file destination
        if not save_path:
            filename = f"shivani_screen_{int(time.time() * 1000)}.png"
            save_path = os.path.join(self.temp_dir, filename)

        img.save(save_path, format="PNG")
        return (save_path, target_monitor, img)

    def capture_region(
        self,
        region: BoundingBox,
        save_path: Optional[str] = None,
    ) -> Tuple[str, Image.Image]:
        """
        Captures a specific rectangular sub-region of the screen.
        Handles coordinate conversions if region is defined in logical coordinates.
        """
        # Capture underlying full screen first to handle multi-monitor offsets and DPI
        full_path, monitor, full_img = self.capture_full_screen()

        transformer = CoordinateTransformer(monitor)
        # If region is logical, map to physical image pixels
        phys_box = transformer.to_physical_box(region)

        # Clamp crop coordinates to image dimensions
        left = max(0, min(full_img.width, int(round(phys_box.left))))
        top = max(0, min(full_img.height, int(round(phys_box.top))))
        right = max(left + 1, min(full_img.width, int(round(phys_box.right))))
        bottom = max(top + 1, min(full_img.height, int(round(phys_box.bottom))))

        cropped_img = full_img.crop((left, top, right, bottom))

        if not save_path:
            filename = f"shivani_region_{int(time.time() * 1000)}.png"
            save_path = os.path.join(self.temp_dir, filename)

        cropped_img.save(save_path, format="PNG")
        return (save_path, cropped_img)
