# Script para crear el acceso directo en el Escritorio
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $projectDir) {
    $projectDir = (Get-Location).Path
}

$desktopPath = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktopPath "Sistema de Ventas.lnk"

$venvPythonw = Join-Path $projectDir ".venv\Scripts\pythonw.exe"
$mainPy = Join-Path $projectDir "main.py"
$iconPath = Join-Path $projectDir "assets\logo.ico"

# Si no existe pythonw en .venv, buscar en el sistema
if (-not (Test-Path $venvPythonw)) {
    $sysPythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
    if ($sysPythonw) {
        $venvPythonw = $sysPythonw
    } else {
        $venvPythonw = "pythonw.exe"
    }
}

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $venvPythonw
$shortcut.Arguments = "`"$mainPy`""
$shortcut.WorkingDirectory = $projectDir
if (Test-Path $iconPath) {
    $shortcut.IconLocation = $iconPath
}
$shortcut.Description = "Sistema de Ventas - Acceso de Empleados"
$shortcut.Save()

Write-Host "Acceso directo creado exitosamente en: $shortcutPath" -ForegroundColor Green
