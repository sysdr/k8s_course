#!/bin/bash
# Stop all containers and remove unused Docker resources (containers, images, volumes, networks).

set -euo pipefail

echo "=== Docker cleanup ==="

if ! command -v docker &>/dev/null; then
  echo "Docker is not installed or not in PATH. Skipping."
  exit 0
fi

echo "Stopping all running containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

echo "Removing all stopped containers..."
docker container prune -f

echo "Removing unused images..."
docker image prune -a -f

echo "Removing unused volumes..."
docker volume prune -f

echo "Removing unused networks..."
docker network prune -f

echo "Running system prune (build cache, etc.)..."
docker system prune -a -f --volumes

echo "=== Docker cleanup complete ==="
