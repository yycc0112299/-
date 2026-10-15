@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0person_tracking\open_rtl_regression.ps1"
if errorlevel 1 pause
