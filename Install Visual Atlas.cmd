@echo off
rem Double-click to install or update Visual Atlas. See README "Get started".
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install-atlas.ps1"
echo.
pause
