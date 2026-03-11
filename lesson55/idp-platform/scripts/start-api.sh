#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_SRC="$PROJECT_ROOT/platform-api/src"
cd "$API_SRC"
export PYTHONPATH="$API_SRC"
export PORT="${PORT:-8000}"
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
