#!/bin/bash
# Stop all containers and remove unused Docker resources (lesson44 / FinOps project)
set -euo pipefail

echo "Stopping all running containers..."
docker stop $(docker ps -q) 2>/dev/null || true

echo "Removing stopped containers..."
docker container prune -f

echo "Removing unused images (dangling and unreferenced)..."
docker image prune -a -f

echo "Removing unused volumes..."
docker volume prune -f

echo "Removing unused networks..."
docker network prune -f

echo "Optional: full system prune (uncomment to use)"
# docker system prune -a -f --volumes

echo "Docker cleanup complete."
