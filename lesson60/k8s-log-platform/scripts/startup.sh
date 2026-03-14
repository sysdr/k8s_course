#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR"
if [ ! -f "local/docker-compose.yaml" ]; then echo "Error: Run setup.sh from lesson60 first. BASE_DIR=$BASE_DIR"; exit 1; fi
echo "Starting stack from $BASE_DIR..."
docker compose -f local/docker-compose.yaml up -d
echo "Waiting for log-api..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  curl -s http://localhost:8000/health/live >/dev/null 2>&1 && break
  sleep 2
done
curl -s http://localhost:8000/health/live && echo "" || echo "log-api may still be starting (check: docker compose -f local/docker-compose.yaml ps)"
echo "Done. Frontend: run from services/log-frontend with npm start (API at http://localhost:8000)"
