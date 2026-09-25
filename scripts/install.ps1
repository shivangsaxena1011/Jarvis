# ==============================================================================
# SHIVANI 1.0 Production Installation Script for Windows (PowerShell)
# ==============================================================================
[CmdletBinding()]
param(
    [string]$InstallDir = "$env:APPDATA\Shivani",
    [switch]$SkipDoctor = $false
)

$ErrorActionPreference = "Stop"

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "         SHIVANI 1.0 - Production Installation            " -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

# 1. Verify Operating System
if ($PSVersionTable.PSEdition -ne "Core" -and [System.Environment]::OSVersion.Platform -ne "Win32NT") {
    Write-Warning "SHIVANI is optimized for Windows 10/11 64-bit."
}

# 2. Setup Application Directories
Write-Host "`n[1/5] Initializing application directory structure at: $InstallDir" -ForegroundColor Yellow
$SubDirs = @("config", "data", "logs", "memory", "tasks", "cache", "backups", "skills", "bin")
foreach ($dir in $SubDirs) {
    $fullPath = Join-Path $InstallDir $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  + Created: $fullPath" -ForegroundColor DarkGray
    }
}

# 3. Locate Python Runtime
Write-Host "`n[2/5] Verifying Python 3.12+ Environment..." -ForegroundColor Yellow
$PythonCmd = $null
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "  + Found 'uv' package manager." -ForegroundColor Green
    $PythonCmd = "uv run python"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pyVersion = python --version 2>&1
    Write-Host "  + Found Python: $pyVersion" -ForegroundColor Green
    $PythonCmd = "python"
} else {
    Write-Error "Python 3.12+ was not found on PATH. Please install Python 3.12 or uv."
}

# 4. Generate CLI Shim / Launcher
Write-Host "`n[3/5] Generating global CLI shim..." -ForegroundColor Yellow
$ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$BinDir = Join-Path $InstallDir "bin"
$ShimPath = Join-Path $BinDir "shivani.cmd"

$ShimContent = @"
@echo off
setlocal
set "PROJECT_ROOT=$ProjectRoot"
set "PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%\.venv\Lib\site-packages;%PYTHONPATH%"
if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    "%PROJECT_ROOT%\.venv\Scripts\python.exe" "%PROJECT_ROOT%\cli\main.py" %*
) else (
    python "%PROJECT_ROOT%\cli\main.py" %*
)
endlocal
"@

Set-Content -Path $ShimPath -Value $ShimContent -Encoding ASCII
Write-Host "  + Created CLI executable: $ShimPath" -ForegroundColor Green

# Add to user PATH if not present
$UserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinDir", "User")
    Write-Host "  + Added $BinDir to User PATH." -ForegroundColor Green
}

# 5. Initialize Default Configuration
Write-Host "`n[4/5] Checking configuration..." -ForegroundColor Yellow
$ConfigPath = Join-Path $InstallDir "config\shivani_config.json"
if (-not (Test-Path $ConfigPath)) {
    $DefaultConfig = @{
        version = "1.0.0"
        environment = "production"
        llm_provider = "gemini"
        llm_model = "gemini-2.5-pro"
        security_policy = "strict"
        voice_enabled = $false
        offline_mode = $false
    } | ConvertTo-Json -Depth 4
    Set-Content -Path $ConfigPath -Value $DefaultConfig -Encoding UTF8
    Write-Host "  + Created default config: $ConfigPath" -ForegroundColor Green
} else {
    Write-Host "  + Existing config preserved: $ConfigPath" -ForegroundColor Green
}

# 6. Run System Doctor Check
Write-Host "`n[5/5] Running SHIVANI System Diagnostics..." -ForegroundColor Yellow
if (-not $SkipDoctor) {
    try {
        & "$ShimPath" doctor
    } catch {
        Write-Warning "Initial doctor check had non-critical warnings. System is still operational."
    }
}

Write-Host "`n===========================================================" -ForegroundColor Green
Write-Host "  SHIVANI 1.0 Installation Complete!" -ForegroundColor Green
Write-Host "  Type 'shivani status' or 'shivani --help' to get started." -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Green
