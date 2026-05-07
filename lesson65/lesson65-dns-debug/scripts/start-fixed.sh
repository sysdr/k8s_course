#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

echo "Starting FIXED environment (all three bugs corrected)"
echo ""

cd "${PROJECT_ROOT}/fixed"
docker compose down --remove-orphans 2>/dev/null || true
docker compose build
docker compose up -d

echo ""
echo "Waiting for log-processor healthcheck to pass (up to 60s)..."
timeout 60 bash -c 'until docker inspect lesson65-processor --format "{{.State.Health.Status}}" 2>/dev/null | grep -q healthy; do sleep 2; echo "  waiting..."; done'
echo ""
echo "=== Container Status ==="
docker compose ps

echo ""
echo "=== Quick Validation ==="
echo "API health check:"
echo "Waiting for API /health to return JSON (up to 60s)..."
timeout 60 bash -c 'until curl -sf http://localhost:8000/health >/dev/null 2>&1; do sleep 2; echo "  waiting..."; done'
curl -sf http://localhost:8000/health | python3 -m json.tool
