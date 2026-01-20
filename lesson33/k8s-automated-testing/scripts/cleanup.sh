#!/bin/bash

set -euo pipefail

echo "=========================================="
echo "  Docker Cleanup Script"
echo "=========================================="
echo ""

cd "$(dirname "$0")/.."

# Stop all running containers
echo "1. Stopping all running containers..."
docker compose down 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true
echo "✓ Containers stopped"
echo ""

# Remove all stopped containers
echo "2. Removing stopped containers..."
docker container prune -f
echo "✓ Stopped containers removed"
echo ""

# Remove unused images
echo "3. Removing unused Docker images..."
docker image prune -a -f
echo "✓ Unused images removed"
echo ""

# Remove unused volumes
echo "4. Removing unused volumes..."
docker volume prune -f
echo "✓ Unused volumes removed"
echo ""

# Remove unused networks
echo "5. Removing unused networks..."
docker network prune -f
echo "✓ Unused networks removed"
echo ""

# Remove build cache
echo "6. Removing build cache..."
docker builder prune -f
echo "✓ Build cache removed"
echo ""

# Show remaining resources
echo "=========================================="
echo "  Remaining Docker Resources"
echo "=========================================="
echo ""
echo "Containers:"
docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "No containers"
echo ""
echo "Images:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null | head -10 || echo "No images"
echo ""
echo "Volumes:"
docker volume ls --format "table {{.Name}}\t{{.Driver}}" 2>/dev/null || echo "No volumes"
echo ""

echo "=========================================="
echo "  Cleanup Complete!"
echo "=========================================="
