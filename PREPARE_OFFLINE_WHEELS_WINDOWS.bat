@echo off
setlocal
cd /d "%~dp0"
echo BRACE 1.0 - prepare matching Windows/Python offline wheels; internet required
call scripts\WINDOWS_PYTHON.bat
if errorlevel 1 goto failed
if not exist "wheelhouse" mkdir "wheelhouse"
"%BRACE_PYEXE%" -m pip download --only-binary=:all: --dest wheelhouse -r requirements-release.txt
if errorlevel 1 goto failed
"%BRACE_PYEXE%" scripts\wheelhouse_manifest.py
if errorlevel 1 goto failed
echo Wheels downloaded and hashed. Test INSTALL_OFFLINE_DEPS_WINDOWS.bat on the target machine.
if not defined BRACE_NONINTERACTIVE pause
exit /b 0

:failed
echo See the error above. Your global Python packages were not changed.
if not defined BRACE_NONINTERACTIVE pause
exit /b 1
