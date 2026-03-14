#!/bin/bash
# Start the full stack (API + frontend in Docker). Open http://localhost:3000 in your browser.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR"
COMPOSE_FILE="local/docker-compose.yaml"
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Error: $COMPOSE_FILE not found. Run setup.sh from lesson60 first."
  exit 1
fi
echo "Starting full stack (API + frontend)..."
docker compose -f "$COMPOSE_FILE" up -d --build
echo "Waiting for services..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health/live 2>/dev/null | grep -q 200; then
    echo "API is up at http://localhost:8000"
    break
  fi
  sleep 2
done
for i in 1 2 3 4 5; do
  if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/ 2>/dev/null | grep -q 200; then
    echo "Frontend is up at http://localhost:3000"
    break
  fi
  sleep 2
done
echo ""
echo "=========================================="
echo "  Open in your browser:"
echo "  http://localhost:3000"
echo "  (API: http://localhost:8000)"
echo "=========================================="
echo ""
echo "If localhost does not work (e.g. WSL), try: http://127.0.0.1:3000"
echo "Send demo logs: $BASE_DIR/scripts/demo.sh"
