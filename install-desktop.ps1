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
$edge = Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'
if (Test-Path $edge) { $shortcut.IconLocation = "$edge,0" }
$shortcut.Save()
Write-Host "Created $shortcutPath"
Write-Host "Double-click Tend to open an app window. Its local server starts automatically if needed."
