#!/bin/bash
# Stop all containers and remove unused Docker resources (containers, images, volumes, networks).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="${SCRIPT_DIR}/k8s-log-platform"

echo "=== Stopping Docker Compose stacks ==="
if [[ -f "${PLATFORM_DIR}/docker-compose.yaml" ]]; then
  (cd "$PLATFORM_DIR" && docker compose down -v 2>/dev/null) || true
fi
docker compose down -v 2>/dev/null || true

echo "=== Stopping all running containers ==="
docker stop $(docker ps -q) 2>/dev/null || true

echo "=== Removing stopped containers ==="
docker container prune -f

echo "=== Removing unused images ==="
docker image prune -a -f

echo "=== Removing unused volumes ==="
docker volume prune -f

echo "=== Removing unused networks ==="
docker network prune -f

echo "=== Removing build cache (optional) ==="
# Uncomment to also clear build cache: docker builder prune -a -f

echo "✅ Cleanup complete."
