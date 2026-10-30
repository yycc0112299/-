$ErrorActionPreference = 'Stop'
$pythonExe = $env:PROJECT_PYTHON
if (!$pythonExe) {
    # Prefer a full CPython installation over the Windows Store app-execution alias.
    $installedPython = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Programs\Python') -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match 'Python3' } |
        Sort-Object FullName -Descending |
        Select-Object -First 1
    if ($installedPython) { $pythonExe = $installedPython.FullName }
}
if (!$pythonExe) {
    $candidate = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($candidate -and $candidate -notmatch '\\WindowsApps\\python\.exe$') { $pythonExe = $candidate }
}
if (!$pythonExe) { throw 'Python not found. Install Python 3.12, set PROJECT_PYTHON, or add Python to PATH.' }
& $pythonExe (Join-Path $PSScriptRoot 'dual_server.py') --browser
