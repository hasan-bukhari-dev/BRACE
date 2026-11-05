@echo off
setlocal
cd /d "%~dp0"
set "BRACE_PORT=8883"
set "BRACE_RUNS_DIR=%~dp0runs\release-demo"
if not exist ".venv\Scripts\python.exe" (
  echo The isolated Python environment is missing. See docs\RESEARCH_FINAL.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" launch.py
if errorlevel 1 pause
