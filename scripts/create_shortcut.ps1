# Script to create Desktop and Project shortcuts for SHIVANI AI
$WshShell = New-Object -ComObject WScript.Shell

$Targets = @()
$OneDriveDesktop = "$env:USERPROFILE\OneDrive\Desktop"
if (Test-Path $OneDriveDesktop) { $Targets += $OneDriveDesktop }

$LocalDesktop = "$env:USERPROFILE\Desktop"
if ((Test-Path $LocalDesktop) -and ($LocalDesktop -ne $OneDriveDesktop)) { $Targets += $LocalDesktop }

$ProjectDir = Split-Path -Parent $PSScriptRoot
if (-not $ProjectDir) { $ProjectDir = (Get-Location).Path }
$Targets += $ProjectDir

foreach ($Dir in $Targets) {
    $LnkPath = Join-Path $Dir "SHIVANI AI.lnk"
    $Shortcut = $WshShell.CreateShortcut($LnkPath)
    $Shortcut.TargetPath = "cmd.exe"
    $Shortcut.Arguments = "/k `"`"$ProjectDir\run.bat`" --open-browser`""
    $Shortcut.WorkingDirectory = $ProjectDir
    $Shortcut.Description = "SHIVANI AI - Personal Autonomous Computer Assistant"
    $Shortcut.IconLocation = "$env:SystemRoot\System32\imageres.dll,198"
    $Shortcut.Save()
    Write-Host "Created shortcut: $LnkPath" -ForegroundColor Green
}
