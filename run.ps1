# SHIVANI AI Launcher
# Automatically finds Python from .venv or system PATH
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $ScriptDir) { $ScriptDir = Get-Location }
$env:PYTHONPATH = "$ScriptDir\.venv\Lib\site-packages;$ScriptDir"

$VenvPython = Join-Path $ScriptDir '.venv\Scripts\python.exe'
if (Test-Path $VenvPython) {
    & $VenvPython "$ScriptDir\main.py" @args
} else {
    python "$ScriptDir\main.py" @args
}
