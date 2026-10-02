$ErrorActionPreference = 'Stop'
$pythonExe = $env:PROJECT_PYTHON
if (!$pythonExe) { $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source }
if (!$pythonExe) { throw 'Python not found. Set PROJECT_PYTHON or add Python to PATH.' }
& $pythonExe (Join-Path $PSScriptRoot 'dual_server.py') --browser
