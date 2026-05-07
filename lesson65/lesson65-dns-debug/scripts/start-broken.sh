#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

echo "Starting BROKEN environment (Lesson 65 — Break-It-Friday)"
echo "Three DNS bugs are active. Run scripts/diagnose.sh to investigate."
echo ""

cd "${PROJECT_ROOT}/broken"
docker compose down --remove-orphans 2>/dev/null || true
docker compose build
docker compose up -d

echo ""
echo "Containers started. Waiting 5 seconds for startup..."
sleep 5

echo ""
echo "=== Container Status ==="
docker compose ps
