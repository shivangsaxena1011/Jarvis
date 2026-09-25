"""SHIVANI Core System Engine"""

import os
import sys
from pathlib import Path

# On Windows, ensure pywin32 directories and DLLs are available if running in virtualenv
if os.name == "nt":
    for candidate in [
        Path(__file__).parent.parent / ".venv" / "Lib" / "site-packages",
    ]:
        if candidate.exists():
            for sub in ["win32", "win32/lib", "pythonwin"]:
                sub_path = str((candidate / sub).resolve())
                if sub_path not in sys.path:
                    sys.path.append(sub_path)
            dll_dir = candidate / "pywin32_system32"
            if dll_dir.exists():
                try:
                    os.add_dll_directory(str(dll_dir.resolve()))
                except Exception:
                    pass

