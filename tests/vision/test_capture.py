"""
Tests for Screen & Window Capture Subsystem.
"""

import os
from vision.capture.monitors import enumerate_monitors, get_primary_monitor
from vision.capture.screen_capture import ScreenCaptureEngine
from vision.capture.window_capture import WindowCaptureEngine
from vision.models.types import BoundingBox, CoordinateSpace


def test_monitor_enumeration():
    monitors = enumerate_monitors()
    assert len(monitors) >= 1
    primary = get_primary_monitor()
    assert primary is not None
    assert primary.width > 0
    assert primary.height > 0
    assert primary.scale_factor >= 1.0


def test_screen_capture_full():
    capture_engine = ScreenCaptureEngine()
    path, mon, img = capture_engine.capture_full_screen()

    assert os.path.exists(path)
    assert os.path.getsize(path) > 0
    assert img.width > 0
    assert img.height > 0
    assert mon.id >= 0


def test_screen_capture_region():
    capture_engine = ScreenCaptureEngine()
    region = BoundingBox(
        x=50.0,
        y=50.0,
        width=200.0,
        height=150.0,
        coordinate_space=CoordinateSpace.LOGICAL,
    )
    path, img = capture_engine.capture_region(region)

    assert os.path.exists(path)
    assert os.path.getsize(path) > 0
    assert img.width >= 100
    assert img.height >= 75


def test_window_capture_info():
    win_engine = WindowCaptureEngine()
    info = win_engine.get_active_window_info()
    assert "title" in info
    assert "rect" in info
    assert info["rect"]["width"] > 0
    assert info["rect"]["height"] > 0
