#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python
echo "SWI V4 Beagle — AUDIT first. AUTHORIZED=NO"
exec "$PY" -m swi_beagle audit --roots "$ROOT/.."
