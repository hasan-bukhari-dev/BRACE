@echo off
setlocal
cd /d "%~dp0"
echo BRACE 1.0 Hatchathon - local research workbench
call scripts\WINDOWS_PYTHON.bat
if errorlevel 1 goto failed
"%BRACE_PYEXE%" -c "import fastapi,uvicorn,numpy,scipy,sklearn,multipart" >nul 2>nul
if errorlevel 1 (
 echo Dependencies are missing. Before the event run SETUP_BRACE_WINDOWS.bat.
 echo For a matching prepared wheelhouse use INSTALL_OFFLINE_DEPS_WINDOWS.bat.
 goto failed
)
"%BRACE_PYEXE%" launch.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo See the error above. Your global Python packages were not changed.
if not defined BRACE_NONINTERACTIVE pause
exit /b 1
