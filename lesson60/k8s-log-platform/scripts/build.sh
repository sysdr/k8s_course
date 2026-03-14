#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR"
docker build -t log-api:latest services/log-api
docker build -t log-processor:latest services/log-processor
cd services/log-frontend && npm install 2>/dev/null; docker build -t log-frontend:latest . 2>/dev/null || true
cd "$BASE_DIR"
echo "Build complete."
