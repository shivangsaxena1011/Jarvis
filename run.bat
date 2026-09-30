@echo off
REM SHIVANI AI Launcher
REM Automatically finds Python from .venv or system PATH
set "PYTHONPATH=%~dp0.venv\Lib\site-packages;%~dp0"

REM Try .venv python first, then system python
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0main.py" %*
) else (
    python "%~dp0main.py" %*
)
