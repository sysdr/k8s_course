#!/bin/bash
# cleanup.sh — Stop containers and remove unused Docker resources for lesson48 Global Log Platform
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/global-log-platform"

echo "=== Stopping Docker Compose (lesson48) ==="
if [[ -d "$PROJECT_DIR" ]] && [[ -f "${PROJECT_DIR}/docker-compose.yaml" ]]; then
  (cd "$PROJECT_DIR" && docker compose down -v --remove-orphans 2>/dev/null) || true
fi
echo "Done."

echo ""
echo "=== Stopping any remaining containers from this project ==="
docker ps -a --filter "name=global-log-platform" -q 2>/dev/null | xargs -r docker rm -f 2>/dev/null || true
echo "Done."

echo ""
echo "=== Removing unused Docker resources ==="
docker container prune -f
docker network prune -f
docker image prune -af --filter "label=com.docker.compose.project=global-log-platform" 2>/dev/null || true
docker image prune -f
echo "Done."

echo ""
echo "=== Removing project artifacts (node_modules, venv, caches) ==="
for dir in "$SCRIPT_DIR" "$PROJECT_DIR"; do
  [[ ! -d "$dir" ]] && continue
  for name in node_modules venv .venv .pytest_cache __pycache__; do
    find "$dir" -type d -name "$name" -prune -exec rm -rf {} + 2>/dev/null || true
  done
  find "$dir" -name "*.pyc" -delete 2>/dev/null || true
done
echo "Done."

echo ""
echo "=== Cleanup complete ==="
