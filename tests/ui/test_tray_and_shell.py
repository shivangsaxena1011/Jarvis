"""
Tests for Desktop Shell modes and System Tray state synchronization.
"""

import pytest
from apps.desktop.shell import DesktopShell, ShellMode
from apps.desktop.tray import SystemTrayManager, TrayStatus


def test_system_tray_status_management():
    tray = SystemTrayManager()
    assert tray.status == TrayStatus.READY
    assert tray.privacy_mode is False
    assert tray.locked is False

    tray.set_status(TrayStatus.WORKING)
    assert tray.status == TrayStatus.WORKING

    tray.set_status(TrayStatus.WAITING_APPROVAL)
    assert tray.status == TrayStatus.WAITING_APPROVAL

    tray.set_status(TrayStatus.OFFLINE)
    assert tray.status == TrayStatus.OFFLINE

    tray.privacy_mode = True
    tray.locked = True
    summary = tray.get_status_summary()
    assert summary["privacy_mode"] is True
    assert summary["locked"] is True


def test_desktop_shell_modes():
    shell = DesktopShell(host="127.0.0.1", port=8000)
    assert shell.mode == ShellMode.DASHBOARD
    assert shell.base_url == "http://127.0.0.1:8000"

    shell.switch_mode(ShellMode.HUD)
    assert shell.mode == ShellMode.HUD

    shell.switch_mode(ShellMode.COMMAND_BAR)
    assert shell.mode == ShellMode.COMMAND_BAR

    shell.switch_mode(ShellMode.TRAY)
    assert shell.mode == ShellMode.TRAY
