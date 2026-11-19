#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ] || [ ! -d frontend/node_modules ]; then
  printf 'Run ./setup.sh before verification.\n' >&2
  exit 1
fi
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
(cd frontend && npm run build)
.venv/bin/python scripts/smoke_server.py
