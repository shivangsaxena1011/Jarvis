$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $ScriptDir) { $ScriptDir = Get-Location }
$env:PYTHONPATH = "$ScriptDir\.venv\Lib\site-packages;$ScriptDir"
& "C:\Users\shiva\AppData\Local\Programs\Python\Python312\python.exe" "$ScriptDir\main.py" @args
