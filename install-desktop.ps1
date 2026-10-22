# Run once from the Tend repository: powershell -ExecutionPolicy Bypass -File .\install-desktop.ps1
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = Join-Path $repo '.venv\Scripts\pythonw.exe'
if (-not (Test-Path $pythonw)) {
    throw "Expected $pythonw. Create the virtual environment and run: .\.venv\Scripts\python.exe -m pip install -e ."
}
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'Tend.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = '-m tend.desktop'
$shortcut.WorkingDirectory = $repo
$shortcut.Description = 'Launch Tend, starting its local services if necessary'
$shortcut.WindowStyle = 1 # Normal app launch; pythonw has no console window
$icon = Join-Path $repo 'tend.ico'
$python = Join-Path $repo '.venv\Scripts\python.exe'
& $python -m tend.windows_icon $icon
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $icon)) { throw 'Unable to generate Tend Windows icon.' }
$shortcut.IconLocation = "$icon,0"
$shortcut.Save()
Write-Host "Created $shortcutPath"
Write-Host "Double-click Tend to start the local services, open the app window, and keep Tend in the system tray."
