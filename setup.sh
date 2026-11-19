#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
python_bin="${PYTHON_BIN:-python3}"
"$python_bin" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ is required"'
node -e 'const [a,b]=process.versions.node.split(".").map(Number); if(a<22 || (a===22 && b<12)) throw Error("Node 22.12+ is required")'
if [ ! -x .venv/bin/python ]; then "$python_bin" -m venv .venv; fi
.venv/bin/python -c 'import sys; from pathlib import Path; assert sys.version_info >= (3, 11); assert sys.prefix != sys.base_prefix; assert "include-system-site-packages = false" in (Path(sys.prefix)/"pyvenv.cfg").read_text(), "Recreate .venv without system site packages"'
.venv/bin/python -m pip install --cache-dir .venv/pip-cache -r requirements.lock.txt
.venv/bin/python -m pip check
(cd frontend && npm ci --no-audit --no-fund --cache ../.venv/npm-cache && npm run build)
.venv/bin/python - <<'PY'
from pathlib import Path
import hashlib
paths = [Path('requirements.txt'), Path('requirements.lock.txt'), Path('frontend/package.json'), Path('frontend/package-lock.json')]
digest = hashlib.sha256(b''.join(p.read_bytes() for p in paths)).hexdigest()
Path('.venv/.setup-inputs').write_text(digest)
PY
printf 'Setup complete. Run ./verify.sh, then ./start.sh.\n'
