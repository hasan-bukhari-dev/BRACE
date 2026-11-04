@echo off
setlocal
cd /d "%~dp0"
call scripts\WINDOWS_PYTHON.bat
if errorlevel 1 goto failed
"%BRACE_PYEXE%" verify_release.py
if errorlevel 1 goto failed
"%BRACE_PYEXE%" -m pytest -q
if errorlevel 1 goto failed
"%BRACE_PYEXE%" scripts\release_smoke.py
if errorlevel 1 goto failed
echo All release checks passed.
if not defined BRACE_NONINTERACTIVE pause
exit /b 0

:failed
echo See the error above. Your global Python packages were not changed.
if not defined BRACE_NONINTERACTIVE pause
exit /b 1
