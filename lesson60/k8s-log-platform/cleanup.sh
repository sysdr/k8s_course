#!/usr/bin/env bash
# cleanup.sh - Stop containers and remove unused Docker resources, then clean project artifacts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Stopping Docker Compose (lesson60 project) ==="
if [ -f "k8s-log-platform/local/docker-compose.yaml" ]; then
  docker compose -f k8s-log-platform/local/docker-compose.yaml down --remove-orphans 2>/dev/null || true
fi

echo "=== Stopping any remaining project containers ==="
docker ps -a --filter "name=local-" --format "{{.ID}}" 2>/dev/null | xargs -r docker rm -f 2>/dev/null || true

echo "=== Removing unused Docker resources ==="
docker container prune -f
docker network prune -f
docker image prune -f
docker volume prune -f
# Optional: uncomment to remove all unused images (dangling + unreferenced)
# docker image prune -a -f

echo "=== Removing project artifacts (node_modules, venv, caches, Istio) ==="
find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "venv" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
[ -d "k8s-log-platform/istio" ] && rm -rf "k8s-log-platform/istio"
find . -type d -name "istio" -exec rm -rf {} + 2>/dev/null || true

echo "=== Cleanup complete ==="
