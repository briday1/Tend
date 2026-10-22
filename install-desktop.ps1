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
$shortcut.WindowStyle = 7 # Minimized as a fallback; pythonw normally creates no window
$icon = Join-Path $repo 'tend.ico'
$python = Join-Path $repo '.venv\Scripts\python.exe'
& $python -m tend.windows_icon $icon
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $icon)) { throw 'Unable to generate Tend Windows icon.' }
$shortcut.IconLocation = "$icon,0"
$shortcut.Save()
Write-Host "Created $shortcutPath"
Write-Host "Use this Tend desktop shortcut (not the browser-installed PWA icon) to start local services automatically."
