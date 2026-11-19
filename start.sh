#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
# Retry a partial installation and refresh changed dependency inputs.
if [ ! -x .venv/bin/python ] || ! .venv/bin/python - <<'PY'
from pathlib import Path
import hashlib, sys
paths = [Path('requirements.txt'), Path('requirements.lock.txt'), Path('frontend/package.json'), Path('frontend/package-lock.json')]
digest = hashlib.sha256(b''.join(p.read_bytes() for p in paths)).hexdigest()
marker = Path('.venv/.setup-inputs')
sys.exit(0 if marker.exists() and marker.read_text() == digest else 1)
PY
then
  ./setup.sh
fi
# Rebuild when source/config has changed, so an old bundle is never served silently.
if [ ! -f frontend/dist/index.html ] || [ -n "$(find frontend/src frontend/index.html frontend/vite.config.ts frontend/tsconfig.json -type f -newer frontend/dist/index.html -print -quit 2>/dev/null)" ]; then
  (cd frontend && npm run build)
fi
exec .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port "${PORT:-8765}"
