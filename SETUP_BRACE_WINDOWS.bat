@echo off
setlocal
cd /d "%~dp0"
echo BRACE 1.0 - dependency setup; internet required
call scripts\WINDOWS_PYTHON.bat
if errorlevel 1 goto failed
if not exist ".venv\Scripts\python.exe" "%BRACE_PYEXE%" -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements-release.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto failed
echo Setup complete. Run RUN_RELEASE_CHECKS_WINDOWS.bat, then START_BRACE_WINDOWS.bat.
if not defined BRACE_NONINTERACTIVE pause
exit /b 0

:failed
echo See the error above. Your global Python packages were not changed.
if not defined BRACE_NONINTERACTIVE pause
exit /b 1
