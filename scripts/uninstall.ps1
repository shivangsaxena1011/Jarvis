# ==============================================================================
# SHIVANI 1.0 Production Uninstallation Script for Windows (PowerShell)
# ==============================================================================
[CmdletBinding()]
param(
    [string]$InstallDir = "$env:APPDATA\Shivani",
    [switch]$KeepData = $false,
    [switch]$BackupFirst = $true,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

Write-Host "===========================================================" -ForegroundColor Red
Write-Host "         SHIVANI 1.0 - System Uninstallation               " -ForegroundColor Red
Write-Host "===========================================================" -ForegroundColor Red

if (-not $Force) {
    $confirm = Read-Host "Are you sure you want to uninstall SHIVANI? (y/N)"
    if ($confirm -notmatch "^[yY]$") {
        Write-Host "Uninstallation cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# 1. Terminate Running Processes
Write-Host "`n[1/4] Stopping active SHIVANI processes..." -ForegroundColor Yellow
$procNames = @("uvicorn", "python", "py")
Get-Process | Where-Object { 
    $_.ProcessName -in $procNames -and ($_.CommandLine -like "*shivani*" -or $_.CommandLine -like "*Jarvis*") 
} | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "  + Running instances stopped." -ForegroundColor Green

# 2. Backup User Data if Requested
if ($BackupFirst -and (Test-Path $InstallDir)) {
    Write-Host "`n[2/4] Creating safety backup of user data..." -ForegroundColor Yellow
    $backupDir = [System.IO.Path]::GetTempPath()
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupZip = Join-Path $backupDir "shivani_pre_uninstall_backup_$timestamp.zip"
    try {
        Compress-Archive -Path "$InstallDir\*" -DestinationPath $backupZip -Force
        Write-Host "  + Safety backup preserved at: $backupZip" -ForegroundColor Green
    } catch {
        Write-Warning "Could not create automatic backup: $_"
    }
} else {
    Write-Host "`n[2/4] Skipping backup." -ForegroundColor DarkGray
}

# 3. Clean up Environment Variables & PATH
Write-Host "`n[3/4] Removing SHIVANI from User PATH..." -ForegroundColor Yellow
$BinDir = Join-Path $InstallDir "bin"
$UserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -like "*$BinDir*") {
    $CleanedPath = ($UserPath -split ";" | Where-Object { $_ -ne $BinDir -and $_ -ne "" }) -join ";"
    [System.Environment]::SetEnvironmentVariable("Path", $CleanedPath, "User")
    Write-Host "  + Removed $BinDir from User PATH." -ForegroundColor Green
}

# 4. Remove Files
Write-Host "`n[4/4] Removing application files..." -ForegroundColor Yellow
if (Test-Path $InstallDir) {
    if ($KeepData) {
        Write-Host "  + Retaining data, memory, and config (-KeepData specified)." -ForegroundColor Cyan
        Get-ChildItem -Path $InstallDir | Where-Object { $_.Name -notin @("data", "memory", "config", "backups") } | Remove-Item -Recurse -Force
    } else {
        Remove-Item -Path $InstallDir -Recurse -Force
        Write-Host "  + Removed $InstallDir" -ForegroundColor Green
    }
}

Write-Host "`n===========================================================" -ForegroundColor Green
Write-Host "  SHIVANI 1.0 Uninstallation Completed." -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Green
