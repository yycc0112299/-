param([int]$Camera=0,[int]$Frames=90,[switch]$Gui)
$ErrorActionPreference='Stop'
$pythonExe=$env:PROJECT_PYTHON
if(-not $pythonExe){$pythonExe=(Get-Command python -ErrorAction SilentlyContinue).Source}
if(-not $pythonExe){$candidate=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe';if(Test-Path -LiteralPath $candidate){$pythonExe=$candidate}}
if(-not $pythonExe){throw 'Python not found. Install Python and dependencies from person_tracking/requirements.txt, or set PROJECT_PYTHON.'}
$bridgeArgs=@((Join-Path $PSScriptRoot 'camera_bridge.py'),'--camera',"$Camera",'--frames',"$Frames")
if($Gui) { $bridgeArgs+='--gui' }
& $pythonExe @bridgeArgs
if($LASTEXITCODE -ne 0) { throw 'Camera capture or ModelSim comparison failed; see output above.' }
