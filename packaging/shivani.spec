# -*- mode: python ; coding: utf-8 -*-
# PyInstaller Spec file for SHIVANI Autonomous AI Computer Agent

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all submodules across shivani packages
hiddenimports = (
    collect_submodules("core")
    + collect_submodules("agents")
    + collect_submodules("tools")
    + collect_submodules("security")
    + collect_submodules("recovery")
    + collect_submodules("observability")
    + collect_submodules("memory")
    + collect_submodules("notifications")
    + collect_submodules("voice")
    + collect_submodules("cli")
    + [
        "uvicorn",
        "fastapi",
        "pydantic",
        "pydantic_settings",
        "rich",
        "httpx",
        "psutil",
        "sqlite3",
        "asyncio",
        "ctypes",
    ]
)

datas = [
    ("apps/desktop", "apps/desktop"),
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "notebook"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Shivani",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Shivani",
)
