@echo off
rem Called from the project root; return an executable path, never a shell fragment.
set "BRACE_PYEXE="
if exist ".venv\Scripts\python.exe" (
  set "BRACE_PYEXE=%CD%\.venv\Scripts\python.exe"
  goto validate
)
if defined BRACE_PYTHON_EXE (
  set "BRACE_PYEXE=%BRACE_PYTHON_EXE%"
  goto validate
)
for %%V in (3.13 3.12 3.11) do (
  for /f "delims=" %%P in ('py -%%V -c "import sys; print(sys.executable)" 2^>nul') do if not defined BRACE_PYEXE set "BRACE_PYEXE=%%P"
)
if not defined BRACE_PYEXE for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined BRACE_PYEXE set "BRACE_PYEXE=%%P"
if not defined BRACE_PYEXE goto missing
:validate
if not exist "%BRACE_PYEXE%" goto missing
"%BRACE_PYEXE%" scripts\check_python.py
if errorlevel 1 goto missing
exit /b 0
:missing
set "BRACE_PYEXE="
echo Compatible standard CPython 3.11-3.13 x64 was not found.
echo Install Python from python.org before the event, or set BRACE_PYTHON_EXE to its full python.exe path.
echo Espressif/ESP-IDF Python is intentionally not used or modified.
exit /b 1
