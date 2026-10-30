@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0live_site\start_dual.ps1"
if errorlevel 1 pause
