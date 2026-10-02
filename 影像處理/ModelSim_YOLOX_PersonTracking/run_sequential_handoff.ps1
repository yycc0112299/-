param([int]$Camera=0,[double]$ASeconds=10,[double]$TransitionSeconds=1,[double]$BSeconds=10,[switch]$NoDisplay)
$ErrorActionPreference='Stop'
$pythonExe=$env:PROJECT_PYTHON
if(-not $pythonExe){$candidate=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe';if(Test-Path -LiteralPath $candidate){$pythonExe=$candidate}}
if(-not $pythonExe){$pythonExe=(Get-Command python -ErrorAction SilentlyContinue).Source}
if(-not $pythonExe){throw 'Python not found. Install Python and dependencies from person_tracking/requirements.txt, or set PROJECT_PYTHON.'}
$argsList=@((Join-Path $PSScriptRoot 'person_tracking\sequential_handoff.py'),'--camera',"$Camera",'--a-seconds',"$ASeconds",'--transition-seconds',"$TransitionSeconds",'--b-seconds',"$BSeconds")
if($NoDisplay){$argsList+='--no-display'}
& $pythonExe @argsList
if($LASTEXITCODE -ne 0){throw 'Single-camera handoff run failed; check camera availability, model assets, and Python dependencies.'}
