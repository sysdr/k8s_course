#!/bin/bash
set -euo pipefail
# cleanup.sh — stop containers and remove unused Docker resources

echo "=== Stopping all Docker Compose services …"
cd "$(dirname "$0")/.." || exit 1
docker-compose down -v 2>/dev/null || true

echo "=== Stopping all related containers …"
docker ps -a --format "{{.Names}}" | grep -E "k8s-log|lesson38" | xargs -r docker stop 2>/dev/null || true
docker ps -a --format "{{.Names}}" | grep -E "k8s-log|lesson38" | xargs -r docker rm -f 2>/dev/null || true

echo "=== Removing unused Docker resources …"
docker system prune -af --volumes 2>/dev/null || true

echo "=== Removing project-specific Docker images …"
docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "k8s-log-tracing-system|lesson38" | xargs -r docker rmi -f 2>/dev/null || true

echo "=== Removing unused networks …"
docker network prune -f 2>/dev/null || true

echo "=== Cleanup complete."
