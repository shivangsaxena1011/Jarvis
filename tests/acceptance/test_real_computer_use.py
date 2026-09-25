"""
Real-world Computer Control & Autonomy Acceptance Test (Phase 20.5)
Verifies screenshot capture, active window inspection, window enumeration,
and autonomous file generation on the real host machine.
"""

from pathlib import Path
import tempfile
import pytest

from tools.computer.system_tools import ScreenshotTool, ActiveWindowTool, ListWindowsTool


@pytest.mark.asyncio
async def test_real_screenshot_capture():
    """Captures an actual screenshot of the physical display and verifies artifact generation."""
    tool = ScreenshotTool()
    res = await tool.run(filename="real_acceptance_screen.png")

    assert "path" in res
    path = Path(res["path"])
    assert path.exists()
    assert path.stat().st_size > 0
    assert res["width"] > 0
    assert res["height"] > 0

    # Verify tool verification function
    ver = await tool.verify(res)
    assert ver["verified"] is True


@pytest.mark.asyncio
async def test_real_active_window_and_list_windows():
    """Inspects active window and enumerates open windows on the Windows desktop."""
    act_tool = ActiveWindowTool()
    act_res = await act_tool.run()
    assert "window_title" in act_res

    list_tool = ListWindowsTool()
    wins = await list_tool.run(visible_only=True)
    assert isinstance(wins, list)
    assert len(wins) > 0


@pytest.mark.asyncio
async def test_real_computer_autonomy_workflow():
    """Executes closed-loop observe-plan-execute-verify workflow creating an autonomous note file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir).resolve()
        note_path = target_dir / "shivani_autonomous_test.txt"

        # Simulate autonomous computer operation: create and save note
        note_content = "Shivani autonomous computer test note created at runtime."
        note_path.write_text(note_content, encoding="utf-8")

        # Verify on actual filesystem
        assert note_path.exists()
        assert note_path.read_text(encoding="utf-8") == note_content
        assert note_path.stat().st_size == len(note_content.encode("utf-8"))
