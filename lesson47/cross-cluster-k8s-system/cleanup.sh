#!/bin/bash
# Lesson 47 / Cross-Cluster K8s: stop all containers and remove unused Docker resources
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/cross-cluster-k8s-system"

echo "=== Stopping services and cleaning Docker ==="

# 1. Stop docker-compose stack if present
if [[ -f "$PROJECT_DIR/docker-compose.yml" ]]; then
  echo "Stopping docker-compose in $PROJECT_DIR..."
  (cd "$PROJECT_DIR" && docker compose down --remove-orphans 2>/dev/null) || true
fi

# 2. Stop any remaining running containers
echo "Stopping all running containers..."
docker stop $(docker ps -q) 2>/dev/null || true

# 3. Remove stopped containers
echo "Removing stopped containers..."
docker container prune -f

# 4. Remove unused images (dangling and unreferenced)
echo "Removing unused images..."
docker image prune -af

# 5. Remove unused volumes
echo "Removing unused volumes..."
docker volume prune -f

# 6. Remove unused networks
echo "Removing unused networks..."
docker network prune -f

# 7. Optional: full system prune (uncomment to use)
# docker system prune -af --volumes

echo "=== Docker cleanup complete ==="
