param([int]$CameraA=0,[int]$CameraB=1,[int]$Frames=30,[switch]$Rtl)
$ErrorActionPreference='Stop'
$pythonExe=$env:PROJECT_PYTHON
if(-not $pythonExe){$pythonExe=(Get-Command python -ErrorAction SilentlyContinue).Source}
if(-not $pythonExe){$candidate=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe';if(Test-Path -LiteralPath $candidate){$pythonExe=$candidate}}
if(-not $pythonExe){throw 'Python not found. Install Python and dependencies from person_tracking/requirements.txt, or set PROJECT_PYTHON.'}
$dualArgs=@((Join-Path $PSScriptRoot 'person_tracking\dual_camera.py'),'--mode','camera','--camera-a',"$CameraA",'--camera-b',"$CameraB",'--frames',"$Frames")
if($Rtl){$dualArgs+='--rtl'}
& $pythonExe @dualArgs
if($LASTEXITCODE -ne 0){throw 'Dual camera run failed; check that two different USB cameras are connected.'}
