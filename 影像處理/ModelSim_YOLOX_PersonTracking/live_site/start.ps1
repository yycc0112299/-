$ErrorActionPreference='Stop'
$url='http://127.0.0.1:8765/'
try {
 $health=Invoke-RestMethod ($url+'api/health') -TimeoutSec 2
 if($health.app -eq 'usb-person-live'){Start-Process $url;exit}
 throw 'Port 8765 is being used by another application.'
} catch {
 if($_.Exception.Message -eq 'Port 8765 is being used by another application.'){throw}
}
$pythonExe=$env:PROJECT_PYTHON
if(-not $pythonExe){$pythonExe=(Get-Command python -ErrorAction SilentlyContinue).Source}
if(-not $pythonExe){$candidate=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe';if(Test-Path -LiteralPath $candidate){$pythonExe=$candidate}}
if(-not $pythonExe){throw 'Python not found. Install Python and dependencies from person_tracking/requirements.txt, or set PROJECT_PYTHON.'}
$script=Join-Path $PSScriptRoot 'server.py'
Start-Process -FilePath $pythonExe -ArgumentList @(('"'+$script+'"'),'--browser') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'server.log') -RedirectStandardError (Join-Path $PSScriptRoot 'server-error.log')
