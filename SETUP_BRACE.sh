#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
PYTHON="${BRACE_PYTHON_EXE:-python3}"
"$PYTHON" -c 'import sys,struct; assert (3,11)<=sys.version_info[:2]<=(3,13) and struct.calcsize("P")==8, "Use standard CPython 3.11–3.13, 64-bit."'
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install -r requirements-release.txt
printf '\nSetup complete. Start with: sh START_BRACE.sh\n'
