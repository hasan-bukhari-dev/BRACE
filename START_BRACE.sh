#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  printf 'Run sh SETUP_BRACE.sh with standard 64-bit CPython first.\n' >&2
  exit 1
fi
exec .venv/bin/python launch.py
