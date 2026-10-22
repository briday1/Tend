# Build a native Windows Tend.exe using WebView2 (no Edge/Chrome app-window identity).
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "Python venv missing. Create .venv and install Tend first." }
Push-Location $repo
try {
    & $python -m pip install -e . "pywebview>=5,<7" "pyinstaller>=6,<7"
    if ($LASTEXITCODE -ne 0) { throw "Native Tend build dependencies failed to install." }
    $icon = Join-Path $repo 'tend-horizon-circle.ico'
    & $python -m tend.windows_icon $icon
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $icon)) { throw "Tend icon generation failed." }

    & $python -m PyInstaller --noconfirm --clean --onefile --windowed --name Tend --icon $icon --distpath (Join-Path $repo 'dist') --workpath (Join-Path $repo 'build') --specpath $repo (Join-Path $repo 'tend\native.py')
    if ($LASTEXITCODE -ne 0) { throw "Native Tend.exe build failed." }

    $exe = Join-Path $repo 'dist\Tend.exe'
    if (-not (Test-Path $exe)) { throw "Missing native executable: $exe" }
    $desktop = [Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktop 'Tend.lnk'
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $exe
    $shortcut.Arguments = ''
    $shortcut.WorkingDirectory = $repo
    $shortcut.Description = 'Tend native desktop app'
    $shortcut.IconLocation = "$exe,0"
    $shortcut.WindowStyle = 1
    $shortcut.Save()
    Write-Host "Native Tend installed: $exe"
    Write-Host "Shortcut created: $shortcutPath"
    Write-Host "Pin dist\Tend.exe or the running native Tend app, not Edge."
} finally { Pop-Location }
