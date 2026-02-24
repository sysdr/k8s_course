#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

if ! [[ -d "$FRONTEND_DIR" ]]; then
  echo "Error: frontend not found at $FRONTEND_DIR"
  exit 1
fi

# Check for duplicate: port 3000 already in use
if command -v lsof &>/dev/null; then
  if lsof -i :3000 2>/dev/null | grep -q LISTEN; then
    echo "Port 3000 already in use. Stop the existing process to avoid duplicate dashboard."
    exit 1
  fi
fi

echo "Starting dashboard at $FRONTEND_DIR (http://localhost:3000)"
cd "$FRONTEND_DIR"
exec npm start
