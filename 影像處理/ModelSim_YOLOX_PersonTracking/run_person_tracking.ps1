param(
 [ValidateSet('camera','web','replay')][string]$Mode='camera',
 [int]$Frames=90,
 [int]$Camera=0,
 [string]$InputDir=''
)
$ErrorActionPreference='Stop'
$pythonExe=$env:PROJECT_PYTHON
if(-not $pythonExe){$pythonExe=(Get-Command python -ErrorAction SilentlyContinue).Source}
if(-not $pythonExe){$candidate=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe';if(Test-Path -LiteralPath $candidate){$pythonExe=$candidate}}
if(-not $pythonExe){throw 'Python not found. Install Python and dependencies from person_tracking/requirements.txt, or set PROJECT_PYTHON.'}
$pipelineArgs=@((Join-Path $PSScriptRoot 'person_tracking\pipeline.py'),'--mode',$Mode,'--frames',"$Frames",'--camera',"$Camera")
if($Mode -eq 'replay') {
 if(-not $InputDir) { throw 'Replay needs -InputDir with a PNG frame directory.' }
 $pipelineArgs+=@('--input-dir',$InputDir)
}
& $pythonExe @pipelineArgs
if($LASTEXITCODE -ne 0) { throw 'Detection/tracking or ModelSim verification failed.' }
