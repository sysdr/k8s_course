#!/bin/bash
# Cleanup: stop containers and remove unused Docker resources
# Run from lesson55 (main directory)

set -euo pipefail

echo "=== Stopping services and Docker cleanup ==="

# Stop local dev processes (API, portal) if running
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "http.server 3000" 2>/dev/null || true
pkill -f "serve.*3000" 2>/dev/null || true
echo "Stopped local dev processes (if any)."

# Stop all running containers
if command -v docker >/dev/null 2>&1; then
  echo "Stopping Docker containers..."
  docker stop $(docker ps -q) 2>/dev/null || true
  docker compose down 2>/dev/null || true

  echo "Removing stopped containers..."
  docker container prune -f

  echo "Removing unused images..."
  docker image prune -a -f

  echo "Removing unused volumes..."
  docker volume prune -f

  echo "Removing unused networks..."
  docker network prune -f

  echo "Full system prune (containers, networks, images, build cache)..."
  docker system prune -a -f

  echo "Docker cleanup complete."
else
  echo "Docker not found, skipping Docker cleanup."
fi

echo "=== Cleanup finished ==="
